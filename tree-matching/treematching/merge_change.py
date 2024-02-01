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
