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


