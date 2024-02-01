import logging, json
from abc import ABC, abstractmethod
from math import inf
from typing import Dict, List, Union

from node import Node, Element, Text
from tree import Tree
from node_path_ids import NodeID
from merge_change import MergeChange, OpType


logger = logging.getLogger(__name__)

class Edit(ABC):
    def __init__(self, affectedID: NodeID = None):
        #affecting the node with the given cpid in the source tree.
        self.cpid: NodeID = affectedID

    @abstractmethod
    def apply(self, subject: Tree) -> None:
        raise NotImplementedError

    @abstractmethod
    def cost(self) -> int:
        raise NotImplementedError

    @abstractmethod
    def __str__(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def get_json(self) -> Dict:
        raise NotImplementedError

    @abstractmethod
    def shadow_apply(self, subject: Tree) -> Dict:
        raise NotImplementedError

    def __lt__(self, other) -> bool:
        if hasattr(other, 'cpid'):
            return self.cpid < other.cpid

    def __eq__(self, other) -> bool:
        if hasattr(other, 'cpid'):
            return self.cpid == other.cpid


class Delete(Edit):
    def __init__(self, node: Node):
        self.source = node
        super().__init__(self.source.id)

    def apply(self, subject: Tree) -> None:
        """Deletes only the source node from the subject tree,
        adds source's children to its parent children list (preserving the order), and then
        updates the child_path_id of all descendants and right siblings descendants.
        """

        # should only lookup the subject nodes using post_id, since
        # post_ids are cached at before applying any of these updates and
        # they are not affected by any possible Delete or Insert updates before
        # this current one. On the other hand, cpids are affected by Delete/Inserts.
        found = subject.find_node_by_post_id(self.source.post_id)
        found_siblings = found.parent.children
        source_index = found_siblings.index(found)
        new_children_list = found_siblings[0:source_index] #does not include source_index
        found_children_size: int = 0
        if isinstance(found, Element):
            new_children_list += found.children
            found_children_size = len(found.children)
            #updates the child_path_ids in addition to parent references
            for i in range(len(found.children)):
                found.children[i].update_parent(found.parent, source_index+i)

        for j in range(source_index+1, len(found_siblings)):
            found_siblings[j].update_id(found_children_size+j-1)
        new_children_list += found_siblings[source_index+1:]
        found.parent.children = new_children_list

    def cost(self) -> int:
        return 1

    def __str__(self) -> str:
        return f'Delete {self.source} with post_id={self.source.post_id}'

    def get_json(self) -> Dict:
        json_rep = {}
        json_rep['type'] = self.__class__.__name__
        json_rep['cpid'] = self.source.id.get_child_path()
        json_rep['tag_name'] = self.source.name
        if isinstance(self.source, Text):
            json_rep['content'] = self.source.content
        return json_rep

    def shadow_apply(self, subject: Tree) -> Dict:
        """Does exactly the same as actual apply, removes the targeted node
        from the subject tree and returns True to keep this in the list of
        JSON updates.
        """
        self.apply(subject)
        return


class Insert(Edit):
    def __init__(self, node: Node):
        if node is None:
            raise ValueError('Cannot insert None into a tree; Expected a Node reference.')
        self.target: Node = node
        # we need to consider the targeted insert index while sorting.
        super().__init__(self.target.id)

    def apply(self, subject: Tree) -> None:
        pass
    def cost(self) -> int:
        return 1

    def __str__(self) -> str:
        return f'Insert {self.target} with post_id={self.target.post_id}'

    def get_json(self) -> Dict:
        """ In the DOM, target cpid either does not exist yet or it is pointing to
        another sibling. We include the parent cpid in the Insert update
        to get the corresponding DOM node, and then insert the child where it
        is expected to be = last element of cpid.
        """
        if self.target.parent is None:
            raise ValueError('Does not support inserting a root node into another tree.')
        json_rep = {}
        json_rep['cpid'] = self.target.parent.id.get_child_path()
        json_rep['i'] = self.target.id.last_child_index()
        if isinstance(self.target, Element):
            json_rep['n'] = self.target.name
            json_rep['attrs'] = self.target.attrs
        else:
            json_rep['c'] = self.target.content
        return json_rep

    def shadow_apply(self, subject: Tree) -> Dict:
        """Inserts only a copy of target node into the subject tree,
        updates the child_path_id of all right siblings descendants.
        The copy of target node should not have any children so that
        the flow of next (Merge) updates becomes the same as what
        happens in the JS patcher.
        Returns true to keep this in the resulting list of JSON updates.
        """
        if self.target.parent is None:
            raise ValueError('Does not support inserting a root node into another tree.')
        parent_id: NodeID = self.target.parent.id
        parent: Node = subject.find_node_by_cpid(parent_id)

        target_index: int = self.target.id.last_child_index()
        # logger.debug(f'Insert into parent id: {parent_id} <- target_insert_index: {target_index}')

        target_copy: Node = self.target.deepcopy_node(parent)
        # target_copy.parent = parent
        if isinstance(self.target, Element):
            target_copy.children = []

        parent.children.insert(target_index, target_copy)

        for j in range(target_index+1, len(parent.children)):
            parent.children[j].update_id(j)

        return


class Merge(Edit):
    def __init__(self, s: Node, t: Node):
        if s.name != t.name:
            logger.debug(f'BIG trouble: src=[pid={s.post_id}]{s} vs target=[pid={t.post_id}]{t}')
            raise ValueError('Cannot merge nodes with names:', s.name, t.name)
        self.source = s
        self.target = t
        self.changes: List[MergeChange] = s.get_merge_changes(t)
        super().__init__(self.target.id)

    def apply(self, subject: Tree) -> None:
        """Merges the source node with the target node such that the equivalent
        node in the subject tree contains only intersection of both nodes,
        either attribute values or text content (mostly becomes empty).
        """
        found = subject.find_node_by_post_id(self.source.post_id)

        # self.changes contains changes which makes the source node exactly the
        # same as target node. Here we only want the common things to remain.
        if isinstance(found, Text):
            if len(self.changes) > 0:
                # the content has changed between the two, o.w. returns empty.
                found.content = ''
        else: # it's an Element
            for c in self.changes:
                if c.change_type == OpType.REMOVE:
                    del found.attrs[c.key]
                elif c.change_type == OpType.CHANGE:
                    # If attr value is a string, we do not want to keep it
                    # Unless it's a data-* attribute with '[' or ']' in it.
                    if type(c.value) == str:
                        if c.key.startswith('data-') and \
                           (c.key.find('[') != -1 or c.key.find(']') != -1):
                            found.attrs[c.key] = ""
                        else:
                            del found.attrs[c.key]
                    # If it's a list, we want the intersection, not the target value
                    else:
                        sourceVals: Set = set(self.source.attrs[c.key])
                        targetVals: Set = set(self.target.attrs[c.key])
                        found.attrs[c.key] = list(sourceVals & targetVals)
                else: #does not apply any ADD attribute or content.
                    pass

    def cost(self) -> int:
        if len(self.changes) > 0:
            return 1
        else:
            return 0

    def __str__(self) -> str:
        return f'Merge node pid={self.source.post_id}{self.source} to {self.target}'

    def get_json(self) -> Dict:
        # If updates are applied in order correctly, then the current DOM tree
        # should have similar structure to the target tree, up to this node.
        json_rep = {}
        json_rep['cpid'] = self.target.id.get_child_path()

        if isinstance(self.target, Element):
            json_rep['n'] = self.target.name # useless
            json_rep['attrs'] = {}
            for c in self.changes:
                if c.change_type == OpType.REMOVE: # TODO: remove attributes how?
                    logger.debug('Did not expect JSON update to remove attrs:'\
                                 f' change={c} -> src={repr(self.source)},'\
                                 f' target={repr(self.target)}')
                    json_rep['attrs'][c.key] = None
                else: # ADD or CHANGE
                    json_rep['attrs'][c.key] = c.value
        else: # get_merge_changes should return one or no change
            # TODO: this should be reverted back to len of 1, assuming we remove all cost 0 edits before this point
            assert(len(self.changes) == 1 or len(self.changes) ==0)
            if len(self.changes) == 1:
                if self.changes[0].change_type == OpType.REMOVE:
                    json_rep['c'] = '' #remove the text content
                else:
                    json_rep['c'] = self.target.content
        return json_rep

    def shadow_apply(self, subject: Tree) -> Dict:
        """Checks to see if the source and target nodes are in the same
        position as they should be or not. If the corresponding node in the
        subject tree is already at the correct position, then returns False.
        As this update does not need to stay in the list of JSON updates,
        assuming it has 0 cost.
        """
        found = subject.find_node_by_post_id(self.source.post_id)
        if found.id != self.target.id:
            # if the updates are applied correctly then the parent of this
            # node should be in the right position ->
            if self.target.is_ancestor(found.parent):
                move_json: Dict = {'cpid': found.id.get_child_path()}
                # detach found from its parent, append to target.parent children
                found.parent.remove_subtree(found)
                # get the corresponding node in subject with target.parent cpid
                expected_parent: Node = subject.find_node_by_cpid(self.target.parent.id)
                expected_parent.append_child(found)

                move_json['np'] = self.target.parent.id.get_child_path()
                move_json['j'] = self.target.id.last_child_index() # for debugging purposes
                return move_json
            else:
                raise ValueError(f'Could not solve the issue with moving:' \
                                 f'found.cpid={found.id} vs. ' \
                                 f'target.cpid={self.target.id}')

        return

