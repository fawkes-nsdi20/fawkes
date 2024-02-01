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

import sys, logging, os
from collections import Counter
from typing import List, Counter

def find_common_paths(first: List, second: List) -> List:
    """ First and second are both lists
    this method returns a list of all common elements in both list
    duplicate elements are ignored. """
    first_set = set(first)
    second_set = set(second)
    intersection = first_set & second_set
    logging.info('<<<--- Fraction of unique common paths --->>>')
    logging.info('# of unique common paths:', len(intersection))
    i1: float = len(intersection)/len(first_set)
    i2: float = len(intersection)/len(second_set)
    logging.info(f'{i1*100:.1f}% of the first & {i2*100:.1f}% of the second.')

    common_paths_list = list(intersection)
    return common_paths_list


def find_counter_intersection(first: List, second: List) -> Counter:
    """ First and second are both lists
    this method returns a list of all common elements in both lists,
    while crossing out the common elements found
    duplicate elements in both lists are counted,
    min of common element counters is returned. """
    first_counter = Counter(first)
    second_counter = Counter(second)
    intersection = first_counter & second_counter
    logging.info('-------------------------')
    first_counter.subtract(intersection)
    logging.info(first_counter.most_common())
    logging.info('-------------------------')
    second_counter.subtract(intersection)
    logging.info(second_counter.most_common())

    return intersection

