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

from tree import Tree
from node import Text, Element

def insert_patchers(common: Tree, patcher_path: str) -> Tree:
    """Inserts main-patcher at the top of html and bottom-patcher at the end.
    Returns the modified tree."""
    # Insert main patcher as the first child of header
    head = common.root.children[0]
    assert(head.name == 'head')
    main_patcher: Element = Element('script', 0, head, {'id': 'main-patcher'})
    head.children.insert(0, main_patcher)
    # read patcher.js content
    with open(patcher_path, 'r') as patcher_file:
        patcher_content: str = patcher_file.read()
        main_patcher.children = [Text(0, main_patcher, patcher_content)]

    # Inserts bottom patcher as the last child of body.
    body = common.root.children[-1]
    assert(body.name == 'body')
    bottom_patcher = Element('script', len(body.children), body, {'id' : 'bottom-patcher'})
    body.children.append(bottom_patcher)

    bottom_content: str =  'var patcher = _getElementById' \
        '.call(document, "bottom-patcher");' \
        'patcher.remove();' \
        'applyJsonUpdates();'
    bottom_patcher.children = [Text(0, bottom_patcher, bottom_content)]
    # Done
