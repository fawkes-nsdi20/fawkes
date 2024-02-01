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

