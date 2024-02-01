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

from typing import List, Union, NamedTuple
from enum import Enum, auto

class OpType(Enum):
    ADD = auto() # the exact value is unimportant
    REMOVE = auto()
    CHANGE = auto()

class MergeChange:
    """Representing one minor change to a node's attributes or text content.
    - change_type is an enum; ADD and REMOVE are mostly used regarding a singular
    attribute of HTML <Element>s. CHANGE is used both for <Element> and <Text>
    nodes.
    - In case source and target are both Text nodes, key is 'content'.
    Otherwise, key is the attribute name.
    - If change_type is REMOVE, value is empty, otherwise
    the value has the updated value for both node types.
    """
    def __init__(self,
                 type_: OpType,
                 key: str,
                 value: Union[List[str], str] = None):
        self.change_type: OpType = type_
        self.key: str = key
        self.value: Union[List[str], str] = value

    def __str__(self):
        return f'({self.change_type.name}, {self.key}, {self.value})'
