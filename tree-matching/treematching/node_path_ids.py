from typing import List

class NodeID:
    def __init__(self, current_index: int, parent_id: 'NodeID' = None):
        try:
            self._root_path: List[int] = parent_id._root_path + [current_index]
        except AttributeError: # parent_id is None
            self._root_path: List[int] = [current_index]

        self._root_len = len(self._root_path)

    def __str__(self):
        return str(self._root_path).replace(' ', '')

    def __hash__(self):
        return hash(self.__str__())

    def __eq__(self, other):
        try:
            if self._root_len != other._root_len:
                return False
            # zip: iterator with the least items decides the length of the result.
            for this_element, other_element in zip(self._root_path, other._root_path):
                if this_element != other_element:
                    return False
            return True
        except:
            return False

    def __lt__(self, other):
        #Attention: We are not restricting the length of two Node IDs to be equal to each other.
        for i in range(min(self._root_len, other._root_len)):
            # _root_path[0..i-1] has been the same so far,
            # if i-th node has lesser index than its counterpart in other_path,
            # then it's on the left side of the other in the same tree
            # and no need to compare the rest of the path.
            # and there is no need to compare the rest of the path.
            if self._root_path[i] < other._root_path[i]:
                return True
            elif self._root_path[i] > other._root_path[i]:
                return False

        # so far _root_path[0..min(_root_lens)] has been the same
        # the path with shortest length is considered smaller.
        return (self._root_len < other._root_len)

    @classmethod
    def from_list(cls, child_path: List[int]) -> 'NodeID':
        """ Creates a NodeID based on the given child_path.
        For unit test only!
        """
        new_id = cls(0, None)
        new_id._root_path = child_path
        new_id._root_len = len(child_path)
        return new_id

    def last_child_index(self) -> int:
        return self._root_path[-1]

    def get_child_path(self) -> List[int]:
        return self._root_path

class PathID:
    def __init__(self, start: NodeID, end: NodeID):
        self.start_node_id: NodeID = start
        self.end_node_id: NodeID = end

    def __str__(self):
        return f'({self.start_node_id} , {self.end_node_id})'

    def __eq__(self, other):
        try:
            return (self.start_node_id == other.start_node_id
                and self.end_node_id == other.end_node_id)
        except:
            return False
