import sys, os, json
from subprocess import check_output, STDOUT
from typing import List, Tuple, Dict

from html_strip import HTMLStrip
from tree import Tree
from node import Node, Text, Element
from edits import Edit, Merge, Insert, Delete
from edit_sequence import EditSequence
from patching_helper import insert_patchers
from config import apted_path, patcher_path

def parse_apted_output(output: str) -> List[Tuple[int, int]]:
    mappings: List[Tuple[int, int]] = []
    except_first_line = output.split('\n')[1:]
    for line in except_first_line:
        parts = line.split('->')
        mappings.append((int(parts[0]), int(parts[1])))
    return mappings

def run_command(command: str) -> str:
    completed = check_output(command, stderr=STDOUT, shell=True) #, check=True)
    return completed[:-1].decode('utf-8')

def compatible_repr_node(current: Node, out) -> None:
    out.write('{')
    if isinstance(current, Element):
        out.write(f'{current.name}') # -{current.post_id}
        for child in current.children:
            compatible_repr_node(child, out)
    else:
        out.write(f'#text')
        out.write(':"'+current.content.replace('"', '\\"')+'"')
    out.write('}')

def compatible_repr(tree: Tree, out_file_path: str) -> None:
    with open(out_file_path, 'w') as out:
        compatible_repr_node(tree.root, out)

def get_apted_edits(first: Tree, second: Tree, out_path: str) -> EditSequence:
    apted_out = run_command(f'java -jar {apted_path} -f {out_path}_1.tree {out_path}_2.tree -m')
    mappings_list: List[Tuple[int, int]] = parse_apted_output(apted_out)

    all_edits: List[Edit] = []
    for mapping in mappings_list:
        source = first.find_node_by_post_id(mapping[0])
        target = second.find_node_by_post_id(mapping[1])

        if mapping[0] == 0: # Insert
            all_edits.append(Insert(target))
        elif mapping[1] == 0: # Delete
            all_edits.append(Delete(source))
        else:
            all_edits.append(Merge(source, target))

    result: EditSequence = EditSequence(all_edits)
    return result


if __name__ == '__main__':

    if len(sys.argv) < 4:
        sys.exit('Usage: python3 treematching/run_apted.py first_html second_html out_path [html|json]')

    first_path = sys.argv[1]
    second_path = sys.argv[2]
    out_path = sys.argv[3]
    goal = "html" # by default

    if len(sys.argv) == 5:
        if sys.argv[4] == "html" or sys.argv[4] == "json":
            goal = sys.argv[4]
        else:
            sys.exit('The 4th (optional) argument can only be "html" or "json"!')

    with open(first_path, 'r') as first_file_handle, \
        open(second_path, 'r') as second_file_handle:

        first_soup = HTMLStrip.from_file(first_file_handle)
        second_soup = HTMLStrip.from_file(second_file_handle)

        first_tree = Tree.from_soup_object(first_file_handle.name, first_soup.original_soup, 1)
        second_tree = Tree.from_soup_object(second_file_handle.name, second_soup.original_soup, 2)

        # Generating the input format needed
        compatible_repr(first_tree, out_path+'_1.tree')
        compatible_repr(second_tree, out_path+'_2.tree')

        all_edits: EditSequence = get_apted_edits(first_tree, second_tree, out_path)
        if goal == 'html':
            common: Tree = all_edits.generate_common_tree(first_tree)
            common.print_html_in_file(out_path)
        else:
            json_out: Dict = all_edits.generate_json_update(first_tree)
            with open(out_path, 'w') as outfile:
                json.dump(json_out, outfile)
            current_dir: str = os.path.dirname(os.path.abspath(__file__))
            patcher_path: str = os.path.join(current_dir, patcher_path)
            # inserts the patcher in place in the common html tree.
            insert_patchers(first_tree, patcher_path)
            first_tree.print_html_in_file(first_path[:-5]+'_patched.html')

