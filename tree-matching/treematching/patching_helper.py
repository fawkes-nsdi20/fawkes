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
