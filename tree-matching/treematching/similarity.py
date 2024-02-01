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

import sys, os
from bs4 import BeautifulSoup

from html_strip import HTMLStrip
from node import Text
from tree import Tree

def no_stripping_compare(first_file_handle, second_file_handle):
    print('<<<--- Original HTML --->>>')
    first_soup = HTMLStrip.from_file(first_file_handle)
    second_soup = HTMLStrip.from_file(second_file_handle)
    return compare_trees(first_soup, second_soup)

def strip_attrs_compare(first_file_handle, second_file_handle):
    print('<<<--- Stripping attributes --->>>')
    first_soup = HTMLStrip.from_file(first_file_handle).strip_attrs()
    second_soup = HTMLStrip.from_file(second_file_handle).strip_attrs()
    return compare_trees(first_soup, second_soup)

def strip_bodies_compare(first_file_handle, second_file_handle):
    print('<<<--- Stripping bodies --->>>')
    first_soup = HTMLStrip.from_file(first_file_handle).strip_bodies()
    second_soup = HTMLStrip.from_file(second_file_handle).strip_bodies()
    return compare_trees(first_soup, second_soup)

def strip_both_preserve_nodes_compare(first_file_handle, second_file_handle):
    print('<<<--- Stripping both attrs and body while preserving nodes --->>>')
    first_soup = HTMLStrip.from_file(first_file_handle).strip_both_preserve_nodes()
    second_soup = HTMLStrip.from_file(second_file_handle).strip_both_preserve_nodes()
    return compare_trees(first_soup, second_soup)

def compare_trees(first_soup: HTMLStrip, second_soup: HTMLStrip) -> float:
    """
    Given the two soup objects, constructs the trees, then
    returns a similarity % as a fraction of shared paths in both trees.
    """
    first_tree = Tree.from_soup_object(first_soup.file_name, first_soup.original_soup)
    second_tree = Tree.from_soup_object(second_soup.file_name, second_soup.original_soup)

    common_paths_size: int = first_tree.num_of_common_paths(second_tree)
    target_size: int = second_tree.total_num_of_paths()
    similarity = float(common_paths_size)*100/target_size
    print(f'{similarity:.2f}')
    return similarity


if __name__ == '__main__':

    if len(sys.argv) < 3:
        sys.exit('Usage: python3.7 treematching/similarity.py first_html second_html')

    first_html_path = sys.argv[1]
    second_html_path = sys.argv[2]

    with open(first_html_path, 'r') as first_file, \
        open(second_html_path, 'r') as second_file:

        no_stripping_compare(first_file, second_file)
        strip_attrs_compare(first_file, second_file)
        strip_bodies_compare(first_file, second_file)
        strip_both_preserve_nodes_compare(first_file, second_file)
