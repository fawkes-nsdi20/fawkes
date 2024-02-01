from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString, Doctype, Comment
import sys, logging, copy

logging.basicConfig(stream=sys.stderr, level=logging.WARNING)

class HTMLStrip:

    def __init__(self, html_file_name, soup):
        self.file_name = html_file_name
        self.original_soup = soup

    """cls is a reference to (this) class object"""
    @classmethod
    def from_file(cls, html_file):
        html_file.seek(0)
        soup = BeautifulSoup(html_file, 'html5lib') # html.parser
        soup_tree = cls(html_file.name, soup)    #calls (this) class constructor
        soup_tree.prepare_html_original()
        soup_tree.strip_meta_nodes()
        return soup_tree

    #TODO: it still has bugs: When we are copying html contents to new array, it messes up the.body, .title relationships for soup object
    """ If the HTML file includes !doctype then soup.contents has more than one child;
        the first child is a DocType Tag,
        the rest of children are either the rest of top-most nodes of html file (like <head> and <body>)
        or one of these children is the top-most html node itself.
        this method will remove the doctype tag and restructures the tree under one top-most <html> tag if necessary
        this method will modify the original_soup reference"""
    def prepare_html_original(self):
        new_content = []
        top_most_html = None
        for child in self.original_soup.contents:
            if isinstance(child, Tag):
                new_content.append(child)
            else:
                if isinstance(child, Doctype):
                    next_sibling = child.find_next_sibling()
                    if(next_sibling.name != u'html'):
                        top_most_html = self.original_soup.new_tag(u'html')

        if top_most_html != None:
            top_most_html.contents = new_content
            self.original_soup.contents = [top_most_html]
        else:
            self.original_soup.contents = new_content

        # logging.info('It is now %d.', len(self.original_soup.contents))
        # logging.info('-------------------------------------')

        # with open('no_doctype.tmp', 'w') as temp_out:
        #     temp_out.writelines("%s\n" % l for l in self.original_soup.prettify().split('\n'))


    def strip_meta_nodes(self):
        assert(len(self.original_soup.contents) == 1)
        self.strip_tag(self.original_soup.contents[0], preserve_nodes = False)

    """ Returns a HTMLStrip object with the same soup object reference """
    def strip_attrs(self):
        assert(len(self.original_soup.contents) == 1)
        # deep_copy_soup = copy.copy(self.original_soup)
        # assert(len(deep_copy_soup.contents) == 1)
        self.strip_tag(self.original_soup.contents[0], strip_attr = True)
        return HTMLStrip(self.file_name, self.original_soup)

    """ Returns a HTMLStrip object with the same soup object reference.
        this method does not remove the attributes, only the bodies. """
    def strip_bodies(self):
        # deep_copy_soup = copy.copy(self.original_soup)
        self.strip_tag(self.original_soup.contents[0], strip_body = True, preserve_nodes = True)
        return HTMLStrip(self.file_name, self.original_soup)

    """ Returns a HTMLStrip object with the same soup object reference.
        this method removes both attributes and bodies for the whole html
        and removes the empty <NavigableString> nodes. """
    def strip_both_attrs_bodies(self):
        assert(len(self.original_soup.contents) == 1)
        self.strip_tag(self.original_soup.contents[0], strip_attr = True, strip_body = True, preserve_nodes = False)
        return HTMLStrip(self.file_name, self.original_soup)

    """ Returns a HTMLStrip object with the same soup object reference.
        this method removes both attributes and bodies for the whole html
        while keeping the empty <NavigableString> nodes. """
    def strip_both_preserve_nodes(self):
        assert(len(self.original_soup.contents) == 1)
        self.strip_tag(self.original_soup.contents[0], strip_attr = True, strip_body = True)
        return HTMLStrip(self.file_name, self.original_soup)


    """ For a given tag, this method strips that tag of its attributes or body or both recursively
        Returns nothing, applies the modification in place. """
    def strip_tag(self, current_tag, strip_attr = False, strip_body = False, preserve_nodes = True):
        # print(f"Mode: strip_attr = {strip_attr} and strip_body = {strip_body}")
        if(strip_attr == True):
            current_tag.attrs = {}

        to_be_removed = []
        for child in current_tag.children:
            if isinstance(child, Tag):
                self.strip_tag(child, strip_attr, strip_body, preserve_nodes)
                if child.name == 'meta':
                    to_be_removed.append(child)

            elif isinstance(child, NavigableString):
                if isinstance(child, Comment):
                    to_be_removed.append(child)
                elif (child.string.isspace()):
                    # if child content is only white spaces
                    to_be_removed.append(child)
                elif strip_body == True:
                    if preserve_nodes:
                        #keeps the node, just removes the text (string)
                        child.string = ''
                    else:
                        to_be_removed.append(child)

        for node in to_be_removed:
            current_tag.contents.remove(node) #it should not throw a ValueError exception


    """ prints the structure of tree recursively """
    def print_tree(self, out_file_name):
        with open(out_file_name, 'w') as out_file:
            self.print_tree_recursive(self.original_soup, 0, out_file)

    def print_tree_recursive(self, current_tag, level, out_file):
        if not isinstance(current_tag, NavigableString):
            out_file.write(f'{"|  "*(level-1)} -- {current_tag.name}\n')
            for child in current_tag.children:
                self.print_tree_recursive(child, level+1, out_file)
        else:
            out_file.write(f'{"|  "*(level-1)} -- \'{current_tag.string}\'\n')


    """returns a list containing all nodes in the tree"""
    def traverse_preorder(self, current_tag):
        nodes = [current_tag.name]
        for child in current_tag.children:
            nodes.extend(self.traverse_preorder(child))
        return nodes

    """ given the current tag (node in the tree) enumerate all paths to the leaves
        returns a list of paths, each path as a string """
    def get_subtree_paths(self, current_tag, delim = ','):
        if isinstance(current_tag, NavigableString):
            if current_tag.name == 'div':
                print('KHODA!')
            return [str(current_tag)]

        paths = []
        for child in current_tag.children:
            sub_paths = self.get_subtree_paths(child, '')
            for sp in sub_paths:
                if(sp != None): #TODO: WHY?
                    # print(type(current_tag), sp)
                    new_path = '<'+current_tag.name+'>'+delim+sp+delim+'<'+current_tag.name+'/>'
                    # print(new_path)
                    paths.append(new_path)

        if(paths == []):
            paths.append(str(current_tag))

        return paths

    """ returns all the paths in the given soup tree """
    # def get_all_paths(self):
        # paths = self.get_subtree_paths(self.original_soup.contents[0], '')
        # i = 0
        # for p in paths:
        #     print(i, p)
        #     i += 1
        # return paths





