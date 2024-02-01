from typing import List

from node_path_ids import PathID
from node import Node

class Path:
    def __init__(self, curr_node: Node, parent_path: 'Path' = None):
        self.able_id: bool = False
        self.nodes: List[Node] = []
        if not parent_path:
            self.nodes = [curr_node]
        else:
            self.nodes = parent_path.nodes + [curr_node]

    def __str__(self):
        result: str = ''
        for n in self.nodes:
            result += n.name+'>'
        if result[-1] == '>':
            result = result[:-1]
        return result

    def __eq__(self, other):
        if not isinstance(other, Path):
            return False
        if len(self.nodes) != len(other.nodes):
            return False
        #TODO: simple optimization is to just look at the very last nodes of this Path
        # since we only call this eq when parent_path of both paths are the same.
        for i in range(len(self.nodes)):
            # without considering the nodes cpids
            if not self.nodes[i].isEqualWOcpid(other.nodes[i]):
                return False
        return True

    def __hash__(self):
        return hash(self.__str__())

    def get_next_level_paths(self) -> List['Path']:
        result: List['Path'] = []
        last_node = self.nodes[-1] # should have at least one node
        try:
            for child in last_node.children:
                result.append(Path(child, self))
        except AttributeError:
            pass # It was a Text node duck-typing
        finally:
            return result

    def length(self):
        return len(self.nodes)


