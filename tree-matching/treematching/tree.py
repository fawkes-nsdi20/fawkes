# MIT License

# Copyright (c) 2019 Shaghayegh Mardani

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import sys, logging
import copy
from collections import deque, Counter
from typing import List, Dict, Union

from node_path_ids import NodeID, PathID
from node import Node, Element
from path import Path
from metrics import find_counter_intersection

logging.basicConfig(stream=sys.stderr, level=logging.DEBUG)

class Tree:
    """Assuming that the given HTML soup object is prepared and optionally stripped
    Creates a parallel structure to the soup tree."""
    def __init__(self, name: str,
                 root: Element,
                 tindex: int):
        self.name: str = name
        self.root: Element = root
        self.tindex: int = tindex

        # List of nodes indexed by post order id
        # A dummy is placed at index 0 because the post order ids start from 1.
        self.nodes: List[Node] = [Element('dummy', 0, None)]
        self.root.set_post_order_id(next_index = 1, nodes = self.nodes)

        # Needed for Zhang and Shasha TED algorithm.
        self.leftmost_leaves: List[Node] = None
        self._cache_leftmost_leaves()


    @classmethod
    def from_soup_object(cls, file_name, soup_obj, tindex = 0):
        assert(len(soup_obj.contents) == 1) #TODO: if not I need to handle it
        root: Element = Node.from_soup_tag(soup_obj.contents[0], 0)
        return cls(file_name, root, tindex) # calls Tree constructor

    def __len__(self) -> int:
        return self.root.post_id

    def deepcopy_tree(self) -> 'Tree':
        root_copy: Element = self.root.deepcopy_node(None)
        tree_copy: Tree = Tree(self.name, root_copy, 3)
        return tree_copy

    def _cache_leftmost_leaves(self) -> None:
        self.leftmost_leaves = [None for i in range(len(self)+1)]
        queue: List[Node] = [self.root]
        while queue:
            current: Node = queue.pop(0)
            self.leftmost_leaves[current.post_id] = current.leftmost_leaf()
            if isinstance(current, Element):
                queue.extend(current.children)

    def find_node_by_post_id(self, id: int) -> Node:
        if (id < 0 or id > len(self.nodes)):
            raise ValueError('Invalid post_id requested: %d', id)
        return self.nodes[id]

    def find_node_by_cpid(self, cpid: NodeID) -> Node:
        current: Node = None
        current_children: List[Node] = [self.root]
        for i, child_index in enumerate(cpid._root_path):
            current = current_children[child_index]
            if isinstance(current, Element):
                current_children = current.children
            else: # Text
                if i != len(cpid._root_path)-1:
                    raise ValueError('Invalid child_path_id (%s) for tree %s', cpid, self.name)
        return current

    def LR_keyroots_ids(self) -> List[int]:
        """Finds LR_keyroot ids in this tree.
        If a node is in LR_keyroots then either that node is root or it has a left sibling.
        Returns a list of ids sorted in increasing order.
        """
        #l_id_dict: mapping leftmost_leaf post_id (l()) to the maximum post_id (among nodes with the same leftmost leaf)
        l_id_dict: Dict[int, int] = {}
        # iterating list of leftmost leaves (except index 0 which is None) in reversed order
        for i in reversed(range(1, len(self)+1)):
            found_id = l_id_dict.get(self.leftmost_leaves[i].post_id, -1)
            if found_id == -1:
                l_id_dict[self.leftmost_leaves[i].post_id] = i

        keys = list(l_id_dict.values())
        keys.sort() #sort returns None, therefore cannot use list def and sort in one line
        return keys

    def get_intersection_paths(self, first_paths: List[Path], second_paths: List[Path]) -> int:
        """ Modified the first(second)_paths in place and only leaves the intersection
        of both list objects in each list --> preserving the object references
        return the size of intersection.
        """
        intersection: Counter[Path, int] = find_counter_intersection(first_paths, second_paths)
        i = 0
        while i < len(first_paths):
            if intersection[first_paths[i]] > 0: # path exists in the intersection
                # this is a super-set of the actual common_paths but ok!
                i += 1
            else:
                # no need to increment prunning the paths which were not in the intersection
                del first_paths[i] # no need to increment i
        # same goes for the other list
        i = 0
        while i < len(second_paths):
            if second_paths[i] in intersection:
                i += 1
            else:
                del second_paths[i] # no need to increment i

        # if done correctly, then
        assert(len(set(first_paths)) == len(intersection))
        assert(len(set(second_paths)) == len(intersection))
        return sum(intersection.values()) # total of all common path counts

    def num_of_common_paths(self, other: 'Tree') -> int:
        total_in_common = 0
        level: int = 1
        first_paths: List[Path] = [self.root.get_path()] # len of 1
        second_paths: List[Path] = [other.root.get_path()] # len of 1
        inter_size: int = self.get_intersection_paths(first_paths, second_paths)
        while inter_size > 0 :
            total_in_common += inter_size
            # add the paths to the next-level nodes based on first(second)_paths
            # assign it back to first(second)_paths and then
            first_next_paths: List[Path] = []
            for i in range(len(first_paths)):
                 first_next_paths += first_paths[i].get_next_level_paths()
            first_paths = first_next_paths

            second_next_paths: List[Path] = []
            for i in range(len(second_paths)):
                 second_next_paths += second_paths[i].get_next_level_paths()
            second_paths = second_next_paths

            # get their intersection again
            inter_size = self.get_intersection_paths(first_paths, second_paths)

        return total_in_common

    def total_num_of_paths(self) -> int:
        # total numbers of paths = total number of nodes
        return self.root.num_of_nodes()

    def __str__(self):
        """Prints the structure of tree recursively."""
        return self.print_tree_recursive(self.root, 0)

    def print_html_in_file(self, out_file_name):
        with open(out_file_name, 'w') as out_file:
            self.root.print_html(out_file)

    def print_tree_recursive(self, current_node, level):
        result = f'{"  |"*(level)}--{str(current_node)}\n'
        if isinstance(current_node, Element):
            for child in current_node.children:
                result += self.print_tree_recursive(child, level+1)
        return result

    def merge_path_w_tree(self, current_path: Path):
        """This works based on the assumption that given path starts from root,
        and for sure the first node on the path is in common with the tree
        and does not require adding to the tree. """
        #assuming that first node of the path is shared
        if not current_path.nodes[0] <= self.root:
            error_msg = f'--> first node on current path: {current_path.nodes[0]}' \
                        f' vs. root_node: {self.root}'
            raise ValueError('Unexpected: First node on the current_path is not root!\n'+error_msg)

        #Index of the current node (on the path) which we are trying to find in the tree,
        #starting from 1 due to above assumption.
        pindex = 1

        # print(f'Path to be merged: {current_path}')
        current_tree_node = self.root #in the tree
        while pindex < current_path.length():
            parent_path_node = current_path.nodes[pindex-1]
            child_path_node = current_path.nodes[pindex]
            # print(f'Debug: PATH: parent: {parent_path_node}, child: {child_path_node}')
            # print(f'Debug: TREE: current:{current_tree_node}')
            assert (current_tree_node.id == parent_path_node.id
                and current_tree_node.name == parent_path_node.name)

            found = current_tree_node.find_equivalent_child(child_path_node)
            if found != None:
                # print(f'Debug: found Eqv child: {found}')
                current_tree_node = found
                pindex += 1
                # continue the loop
            else:
                print(f'Debug: adding the child {child_path_node} to {current_tree_node}')
                current_tree_node.add_child(child_path_node)
                # print(f'Debug: after adding: {current_tree_node}')
                return

