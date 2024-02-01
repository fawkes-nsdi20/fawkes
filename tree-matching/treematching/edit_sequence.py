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

import logging, json
from typing import List, Dict, Union

from tree import Tree
from edits import Edit, Delete, Insert, Merge

logger = logging.getLogger(__name__)

# helper function for json minimization
def _is_direct_parent(parent: Dict, next_edit: Dict) -> bool:
    return next_edit.get('t') == parent.get('t') and \
        next_edit['cpid'][:-1] == parent['cpid'] and \
        next_edit['cpid'][-1] == parent.get('i') # parent might not have i


class EditSequence:
    # Not passing [] as a default argument because of: https://docs.python-guide.org/writing/gotchas/
    def __init__(self, edits: List[Edit] = None, cost: int = -1):
        self.edits_json_list: List[Dict] = []
        self.total_cost: int = cost
        if edits is None:
            self.edits = []
            self.total_cost = 0
        else:
            self.edits: List[Edit] = sorted(edits)
            if cost == -1:
                self.total_cost = 0
                for e in self.edits:
                    self.total_cost += e.cost()

    @classmethod
    def append(cls, left_subtree: 'EditSequence', recent_edits: Union[Edit, 'EditSequence']):
        """Creates a new instance of EditSequence by adding the recent_edits to
        the previous edit sequence (left_subtree, before this point).
        recent_edits could be just one Edit or another EditSequence, therefore we need to check
        the type of parameter passed into the function.
        Attn: For now, we are NOT optimizing consecutive delete or insert costs.
        therefore we are computing total_cost beforehand, instead of on-the-fly.
        #TODO: consider optimizing consecutive deletes/inserts
        """
        # on purpose shallow copy; no need to deep copy all edit elements
        new_edits: List[Edit] = left_subtree.edits.copy()
        new_total_cost: int = left_subtree.total_cost
        if isinstance(recent_edits, Edit):
            new_edits.append(recent_edits)
            new_total_cost += recent_edits.cost()
        elif isinstance(recent_edits, EditSequence):
            new_edits.extend(recent_edits.edits)
            new_total_cost += recent_edits.total_cost
        else:
            raise TypeError('This method expects an object of type either Edit or EditSequence!')

        return cls(new_edits, new_total_cost)

    def __str__(self):
        return f'cost = {self.total_cost}, edits = [{", ".join(map(str, self.edits))}]'

    def __repr__(self):
        nl = '\n'
        return f'total_cost = {self.total_cost}, edits = {nl.join(map(repr, self.edits))}'

    def filter_out_edits(self, edit_class) -> None:
        # does not change the order of edits -> they are kept sorted.
        filtered: List[Edit] = []
        for edit in self.edits:
            if not isinstance(edit, edit_class):
                filtered.append(edit)
            else:
                self.total_cost -= edit.cost()
        self.edits = filtered


    def _minimize_json(self, index: int) -> None:
        parent: Dict = self.edits_json_list[index]
        next_index = index+1
        while next_index < len(self.edits_json_list) and \
            _is_direct_parent(parent, self.edits_json_list[next_index]):
            self._minimize_json(next_index)
            parent_content: List = parent.get('c')
            if parent_content is None:
                parent['c'] = []
            child_json: Dict = self.edits_json_list[next_index]
            del child_json['cpid']
            del child_json['i']
            parent['c'].append(child_json)
            # removes this edit from the list => next_index refers to the next edit not seen so far
            del self.edits_json_list[next_index]

        # further minimization: if parent (element) has only one TextContent child
        # then remove the children array (first 'c' value) and replace it
        # with just the content string
        children: List[Dict] = parent.get('c')
        #if parent is an element node with exactly one child
        if parent.get('n') and children and len(children) == 1:
            if children[0].get('n') is None: # the only child is a TextContent
                parent['c'] = children[0]['c']


    def generate_json_update(self, source: Tree) -> Dict:
        """Returns a JSON representation of all the edits.
        Before generating a JSON for each edit, it calls shadow_apply
        to simulate what happens in the DOM.
        This is particularly important when a node is to be inserted in the Tree
        but then it's children are already existing (not removed) in the source
        tree. So we need to look at the (Merge) edits concerning those children,
        and make sure to include updates for JS patcher to move these node to
        their correct position in the tree.
        In case shadow_apply returns a move update, it includes it in the JSON.
        """
        # map_iterator = map(lambda e: e.get_json(), sorted(self.edits))
        # self.edits_json_list = list(map_iterator)
        self.edits_json_list = []
        subject: Tree = source.deepcopy_tree()
        for edit in self.edits:
            move_json: Dict = edit.shadow_apply(subject)
            if move_json:
                self.edits_json_list.append(move_json)
            if edit.cost() > 0:
                self.edits_json_list.append(edit.get_json())

        # minimizing json output by merging some edits in one json object
        i = 0
        # _minimize_json() might shrink edits_json_list => check len() each call
        while i < len(self.edits_json_list):
            self._minimize_json(i)
            i += 1

        json_rep = {'edits': self.edits_json_list}
        return json_rep


    def generate_common_tree(self, source: Tree) -> Tree:
        """Given the source tree, it returns a (HTML) tree which only includes
        nodes/attributes/contents which are in common between both trees.
        To do so, first we filter out all Inserts. Then transform all script
        -related edits. Finally, we start applying the remaining Merge/Deletes
        on a deepcopy of source tree. Merge.apply() will take care of removing
        attributes/contents which are not in common.
        """
        self.filter_out_edits(Insert)
        # Deleting all <script>...</script>s which are below another edit.
        # Basically every script-related edit, besides starting Merges
        # with 0-cost (if any) is transformed to Delete.
        delete_scripts: bool = False
        for (index, edit) in enumerate(self.edits):
            if not delete_scripts:
                if edit.cost() == 0: # Only a Merge cost can be 0
                    continue;
                else:
                    # logger.info('Here is where we start cutting the scripts: '\
                    #             f'{index}, {edit}')
                    delete_scripts = True;
            # go on and transform edit to Delete if needed.
            if edit.source.name == 'script':
                if isinstance(edit, Merge):
                    self.edits[index] = Delete(edit.source) # Merge -> Delete
                    # Check if script has a content which should be next update.
                    if index+1 < len(self.edits) and \
                       self.edits[index+1].source.parent == edit.source:
                        self.edits[index+1] = Delete(self.edits[index+1].source)
                else: #already a Delete edit on a script
                    if index+1 < len(self.edits):
                        next_edit: Edit = self.edits[index+1]
                        # if next edit is about content of this script
                        if next_edit.source.parent.id == edit.source.id:
                            assert(isinstance(next_edit, Delete))

        # Note: self.edits are sorted beforehand.
        common_tree: Tree = source.deepcopy_tree()
        for edit in self.edits:
            edit.apply(common_tree)

        return common_tree
