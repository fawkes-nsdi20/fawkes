import logging
from typing import List, Dict, Union
from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString
from abc import ABC, abstractmethod
from math import inf

from node_path_ids import NodeID
from merge_change import MergeChange, OpType
# from path import Path

logger = logging.getLogger(__name__)

class Node(ABC):
    def __init__(self,
                name: str,
                current_index: int,
                parent: 'Node') -> 'Node':
        self.name: str = name
        parent_id: NodeID = parent.id if parent != None else None
        self.id: NodeID = NodeID(current_index, parent_id)
        self.parent: Node = parent
        self.post_id: int = -1
        self.path = None


    @classmethod
    def from_soup_tag(cls,
                soup_tag, #: bs4.element.Tag/NavigableString
                current_index: int,
                parent: 'Element' = None) -> 'Node':
        """Given a Tag in the soup tree, this method creates Node objects
        corresponding to the given Tag and all of its decedents, preserving the order.
        cls: a reference to (this) class. It is used to call the Node constructor.
        soup_tag: bs4.element.Tag/NavigableString node the in soup tree.
        current_index: this node's index in its parents 'children' collection.
        """
        if isinstance(soup_tag, NavigableString):
            return Text(current_index, parent, text = str(soup_tag.string))

        assert(type(soup_tag) == Tag)
        node = Element(soup_tag.name, current_index, parent, soup_tag.attrs)
        # If <noscript> then it should only have one Text child.
        # The Text child content is set to string of original children nodes.
        if soup_tag.name == 'noscript':
            if len(soup_tag.contents) > 0:
                content_str: str = ''.join(map(str, soup_tag.contents))
                node.children = [Text(0, parent = node, text = content_str)]
        else:
            children: List[Node] = []
            for index in range(len(soup_tag.contents)):
                child_node = Node.from_soup_tag(soup_tag.contents[index],
                                                index,
                                                parent = node)
                children.append(child_node)
                node.children = children
        return node

    @classmethod
    def from_text(cls,
                  html_str: str) -> 'Node':
        """Constructs a sub-tree from the given piece of html.
        For unit test only!
        """
        soup_tag = BeautifulSoup(html_str, 'html.parser')
        return cls.from_soup_tag(soup_tag.contents[0], current_index = 0)

    def __repr__(self):
        return self.__str__()

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def __hash__(self):
        #Attention: is used to check equality of two instances in a Set
        return hash(self.__str__())

    @abstractmethod
    def __eq__(self, other):
        pass

    @abstractmethod
    def isEqualWOcpid(self, other):
        pass

    @abstractmethod
    def deepcopy_node(self, parent: 'Element') -> 'Node':
        pass

    def update_id(self, new_index: int) -> None:
        """Updates the child path id based on the parent child_path_id and the given new index.
        The new index is the (updated) index of this node inside parent's list of children.
        Here we are reading the parent.id again, because it probably has changed since the construction of this node.
        """
        old_id = self.id
        self.id = NodeID(new_index, self.parent.id)

    def update_parent(self, new_parent: 'Node', new_index: int) -> None:
        self.parent = new_parent
        self.update_id(new_index)

    @abstractmethod
    def set_post_order_id(self, next_index: int, nodes: List['Node']) -> int:
        """Traverses the sub-tree of this node in a post-order manner.
        Given next available index, it sets post_ids for all of its children recursively
        and then sets the id for itself. Also caches the nodes by post id,
        such that element at index i of nodes array has post_id = i
        Returns the next available index.
        """
        raise NotImplementedError

    @abstractmethod
    def print_html(self, out_file) -> None:
        """Write valid HTML corresponding to subtree of this node to the given out_file handle."""
        pass

    @abstractmethod
    def leftmost_leaf(self) -> 'Node':
        """Returns the leftmost leaf descendant of this subtree."""
        pass

    def find_node_by_post_id(self, id: int) -> 'Node':
        if self.post_id == id:
            return self

    def transform_cost(self, other: 'Node') -> float:
        """Considers the possibility of transforming this node to the other node.
        1) If the node tag names and attributes/text contents are the same,
        then transformation cost is 0.
        2) In case the node tag names are the same but some of attributes/the text content
        is different then transformation cost is 1 (for now).
        3) It is impossible to do any modifications if nodes tag names are not the same.
        In this case, the cost is considered +infinity.
        """
        # Keeping this only for TreeMatching class.
        # TODO: Refactor this later and separate from APTED.
        try:
            changes: List = self.get_merge_changes(other)
            if len(changes) > 0:
                return 1
            else:
                return 0
        except ValueError:
            return inf

    @abstractmethod
    def get_merge_changes(self, other: 'Node',
                          intersect: bool) -> List[MergeChange]:
        raise NotImplementedError

    @abstractmethod
    def print_html_tag(self) -> str:
        raise NotImplementedError

    def is_ancestor(self, other: 'Node') -> bool:
        """Checks if the other node is an ancestor of this node."""
        ancestor = self.parent
        while ancestor:
            if ancestor.id == other.id and \
               ancestor.name == other.name:
                # The two nodes might not be exactly the same, only need
                # their cpid and name to be the same. Since there might be
                # other Insert/Deletes on their children later that makes these
                # two equal to each other. Also we ignore merging attributes in
                # the shadow_apply for now.
                return True
            if ancestor.id == other.id:
                logger.error(f'Found ancestor={ancestor} with same id,'\
                             f'but not equal to other={other}')
            ancestor = ancestor.parent
        return False

    @abstractmethod
    def list_uris(self, urls: List[str]) -> str:
        raise NotImplementedError

    def get_path(self) -> 'Path':
        """Returns the path from root to this node.
        It also saves the path in a field for future use.
        """
        from path import Path
        if not self.path:
            if not self.parent:
                self.path = Path(self, parent_path = None)
            else:
                self.path = Path(self, self.parent.get_path())
        return self.path

    @abstractmethod
    def num_of_nodes(self) -> int:
        """Returns the total number of nodes in this subtree including root."""
        pass

class Text(Node):
    def __init__(self,
                current_index: int,
                parent: 'Node',
                text: str) -> 'Text':
        self.content: str = text
        Node.__init__(self,
                    name = 'text',
                    current_index = current_index,
                    parent = parent)

    def __repr__(self):
        return f'{{{self.id}: {self.name}, \'{self.content}\'}}'

    def __str__(self):
        return f'{{{self.id}: {self.name}}}'

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        if not isinstance(other, Text):
            return False
        return (self.id == other.id) and (self.content == other.content)

    def isEqualWOcpid(self, other):
        if not isinstance(other, Text):
            return False
        return (self.content == other.content)

    def deepcopy_node(self, parent: 'Element') -> 'Text':
        return Text(self.id.last_child_index(), parent, self.content)

    def print_html(self, out_file) -> None:
        out_file.write(self.content)

    def set_post_order_id(self, next_index: int, nodes: List['Node']) -> int:
        self.post_id = next_index
        nodes.append(self)
        # assert(nodes[self.post_id] == self)
        return next_index+1

    def leftmost_leaf(self) -> Node:
        return self

    def get_merge_changes(self, other: Node) -> List[MergeChange]:
        """Returns a list of MergeChange containing one or no change.
        If content has not changed, it returns an empty list.
        Otherwise, it returns a CHANGE to the target content.
        Unless this (source) content is empty, then ADD the target content,
        or other (target) content is empty, then REMOVE the content.
        Assumption is that if node.content becomes empty in the common_html,
        it is not parsed as an empty TextNode when running APTED.
        """
        if not isinstance(other, Text):
            raise ValueError('[Merge] other node is not TextNode!')
        if self.content == other.content:
            return []
        if self.content == '':
            return [MergeChange(OpType.ADD, "content", other.content)]
        if other.content == '':
            return [MergeChange(OpType.REMOVE, "content")]

        return [MergeChange(OpType.CHANGE, "content", other.content)]

    def print_html_tag(self) -> str:
        return self.content

    def list_uris(self, urls: List[str]) -> str:
        # does not need to do anything
        return ''

    def num_of_nodes(self) -> int:
        return 1


class Element(Node):
    def __init__(self,
                name: str,
                current_index: int,
                parent: 'Element',
                attrs: Dict[str, Union[List[str], str]] = {},
                children: List[Node] = []) -> 'Element':
        self.attrs: Dict[str, Union[List[str], str]] = attrs
        self.children: List[Node] = children
        Node.__init__(self,
                    name = name,
                    current_index = current_index,
                    parent = parent)

    def __str__(self):
        output: str = f'{{{self.id}: {self.name}, '
        if self.attrs != {}:
                output += str(self.attrs)+', '
        output += f'#children={len(self.children)}}}'
        return output

    def __repr__(self):
        output: str = f'{{{self.id}: {self.name}, '
        if self.attrs != {}:
            output += str(self.attrs)+', '
        # children: str = '\n'.join(map(str, self.children))
        output += f'#children={len(self.children)}}}'
        return output

    def __eq__(self, other):
        #Attention: Not considering list of children in this comparison!
        if not isinstance(other, Element):
            return False
        return ((self.id == other.id)
                and (self.name == other.name)
                and (self.attrs == other.attrs))

    def isEqualWOcpid(self, other):
        if not isinstance(other, Element):
            return False
        return ((self.name == other.name)
                and (self.attrs == other.attrs)) #TODO: better comparison of attrs

    def __hash__(self):
        return hash(self.__str__())

    def __le__(self, other):
        if not isinstance(other, Element):
            return False
        return (self.id == other.id and self.name == other.name)

    def deepcopy_node(self, parent: 'Element') -> 'Element':
        element_copy = Element(self.name, self.id.last_child_index(), parent)
        attrs_copy: Dict[str, Union[List[str], str]] = {}
        for name, value in self.attrs.items():
            attrs_copy[name] = value
        element_copy.attrs = attrs_copy
        children_copy = []
        for child in self.children:
            children_copy.append(child.deepcopy_node(parent=element_copy))
        element_copy.children = children_copy
        return element_copy

    def update_id(self, new_index: int) -> None:
        super().update_id(new_index)
        for i in range(len(self.children)):
            self.children[i].update_id(i)

    #TODO(!!): stripping strategy -> right now we are ignoring attributes
    def find_equivalent_child(self, node: Node) -> Node:
        """Finds equivalent of given node in this list of children.
        We consider two nodes equivalent if their ids and names match.
        The reason we are not using <if node in self.children> directly is that we want
        the exact child (object) in children list as it might have some different descendants
        down the line, compared to the given node (which comes from another tree/path).
        """
        for child in self.children:
            if child.id == node.id and child.name == node.name:
                return child
        return None

    def add_child(self, child_node: Node):
        #Attention: Assuming that list of children are sorted based on NodeID
        for index in range(len(self.children)):
            if self.children[index].id > child_node.id:
                self.children.insert(index, child_node)
                return
            elif self.children[index].id == child_node.id:
                raise ValueError(f'Did not expect one of the child IDs to be equal to-be-added-node ID')

        # print('child node before append', child_node)
        self.children.insert(len(self.children), child_node)
        # print(self.children[0])
        # print('before return = ', child_node)
        return

    def _get_attrs_str(self) -> str:
        """Returns a string representation of attributes with valid HTML syntax.
        Returned string includes a leading space, used after the tag name.
        """
        output: str = '' # f' cpid="{self.id}"'
        for name, value in self.attrs.items():
            if type(value) != str:
                value = ' '.join(value)
            else:
                value = value.replace('"', '&quot;')
            output += f' {name}=\"{value}\"'
        return output

    def print_html(self, out_file) -> None:
        #void elements -> they do not have any children, self-closing tags
        if self.name in ['garea', 'base', 'br', 'col', 'embed', 'hr', 'img', \
                        'input', 'link', 'meta', 'param', 'source', 'track', 'wbr']:
            out_file.write(f'<{self.name}{self._get_attrs_str()}/>')
            assert(len(self.children) == 0)
        else:
            out_file.write(f'<{self.name}{self._get_attrs_str()}>')
            for child in self.children:
                child.print_html(out_file)
            out_file.write(f'</{self.name}>')

    def find_element_by_attr(self, key: str, value: str):
        """Finds the first occurrence of an element which has an attribute (key-value pair)
        equal to the one given.
        """
        found_value = self.attrs.get(key, None)
        if found_value is not None:
            if isinstance(found_value, list) and value in found_value:
                return self
            elif isinstance(found_value, str) and value == found_value:
                return self
        for child in self.children:
            if isinstance(child, Element):
                result = child.find_element_by_attr(key, value)
                if result is not None:
                    return result
        return None

    def set_post_order_id(self, next_index: int, nodes: List['Node']) -> int:
        for child in self.children:
            next_index = child.set_post_order_id(next_index, nodes)
        self.post_id = next_index
        nodes.append(self)
        # assert(nodes[self.post_id] == self)
        return next_index+1

    def leftmost_leaf(self) -> Node:
        if len(self.children) > 0:
            return self.children[0].leftmost_leaf()
        else:
            return self

    def find_node_by_post_id(self, id: int) -> Node:
        if self.post_id == id:
            return self
        for child in self.children:
            if child.post_id > id:
                return child.find_node_by_post_id(id)
            elif child.post_id == id:
                return child

        raise RuntimeError('Could not find a node with id =', id)

    def get_merge_changes(self, other: Node) -> List[MergeChange]:
        """Returns a list of MergeChange by comparing values of both elements
        attributes. Attributes could have been removed from this(source) node,
        added to the other (target) node, or changed. If an attribute value is
        changed and intersect is true, then intersection of both values
        is returned, otherwise target value is returned as a part of change.
        If the given node is not an Element returns a ValueError."""
        if self.name != other.name:
            raise ValueError('[Merge] this & other are not the same type!')

        changes: List[MergeChange] = []
        for attr_name, this_value in self.attrs.items():
            other_value = other.attrs.get(attr_name)
            if other_value == None: # does not exist in the other element
                changes.append(MergeChange(OpType.REMOVE, attr_name))
            elif other_value != this_value: # there was a change in value
                # to make sure that lists are not just reordered
                intersection: Set = set(this_value) & set(other_value)
                if type(this_value) == str or \
                   intersection != set(other_value):
                    changes.append(MergeChange(OpType.CHANGE,
                                               attr_name,
                                               other_value))

        for attr_name, that_value in other.attrs.items():
            this_value = self.attrs.get(attr_name)
            if this_value == None:
                changes.append(MergeChange(OpType.ADD, attr_name, that_value))

        return changes

    #TODO: merge this with the already existing print_html method
    def print_html_tag(self) -> str:
        if self.name in ['garea', 'base', 'br', 'col', 'embed', 'hr', 'img', \
                         'input', 'link', 'meta', 'param', 'source', 'track', 'wbr']:
            return f'<{self.name}{self.get_attrs()}/>\n'

        else:
            return f'<{self.name}{self.get_attrs()}></{self.name}>\n'

    def append_child(self, child: Node) -> None:
        appended_index: int = len(self.children)
        self.children.append(child)
        child.parent = self
        # recursively updates the cpids of all nodes in the subtree.
        child.update_id(appended_index)

    def remove_subtree(self, to_be_removed: Node) -> None:
        """Removes the subtree rooted at the given to_be_removed node from this node."""
        remove_index: int = -1
        for i, child in enumerate(self.children):
            if child == to_be_removed:
                remove_index = i
            # we are on the right side of to_be_removed node
            if remove_index != -1:
                child.update_id(i-1)

        self.children.pop(remove_index) # == .remove(child)

    def list_uris(self, uris_so_far: List[str]) -> str:
        base_url : str = ''
        found_uri: str = ''
        if self.name == 'link' and \
           self.attrs.get('href'):
            found_uri = self.attrs['href']
        elif self.name == 'script' and \
             self.attrs.get('src'):
            found_uri = self.attrs['src']
        elif self.name == 'img' and \
             self.attrs.get('src'):
            found_uri = self.attrs['src']
            # <source> <video> <audio>
        elif self.name == 'base' and \
             self.attrs.get('href'):
            base_url = self.attrs['href']

        if found_uri != '' and \
           not found_uri.startswith('data') and \
           not found_uri.startswith('android-app:') and \
           not found_uri.startswith('ios-app:'):
            uris_so_far.append(found_uri.strip())

        for child in self.children:
            base_url += child.list_uris(uris_so_far)

        return base_url

    def num_of_nodes(self) -> int:
        num: int = 1
        for child in self.children:
            num += child.num_of_nodes()
        return num
