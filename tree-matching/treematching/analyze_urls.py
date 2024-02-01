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

from sys import argv, exit
from typing import List, Union
from bs4 import BeautifulSoup
from bs4.element import Tag, NavigableString, Doctype

def parse_html(html_file_handle):
    # returns the soup object of tree's root
    soup_obj = BeautifulSoup(html_file_handle, 'html5lib')
    new_content = []
    top_most_html = None
    for child in soup_obj.contents:
        if isinstance(child, Tag):
            new_content.append(child)
        else:
            if isinstance(child, Doctype):
                next_sibling = child.find_next_sibling()
                if(next_sibling.name != u'html'):
                    top_most_html = soup_obj.new_tag(u'html')
    if top_most_html != None:
        top_most_html.contents = new_content
        return top_most_html
    else:
        return new_content[0]


def list_uris(soup_tag: Union[Tag, NavigableString],
                uris_so_far: List[str]) -> str:
    if isinstance(soup_tag, NavigableString):
        return ''
    # If <noscript> should only have one Text child.
    if soup_tag.name == 'noscript':
        return ''
    base_url : str = ''
    found_uri: str = ''
    if soup_tag.name == 'link' and \
        soup_tag.attrs.get('href'):
        found_uri = soup_tag.attrs['href']
    elif soup_tag.name == 'script' and \
            soup_tag.attrs.get('src'):
        found_uri = soup_tag.attrs['src']
    elif soup_tag.name == 'img' and \
        soup_tag.attrs.get('src'):
        found_uri = soup_tag.attrs['src']
        # <source> <video> <audio>
    elif soup_tag.name == 'base' and \
        soup_tag.attrs.get('href'):
        base_url = soup_tag.attrs['href']
    if found_uri != '' and \
        not found_uri.startswith('data') and \
        not found_uri.startswith('android-app:') and \
        not found_uri.startswith('ios-app:'):
        uris_so_far.append(found_uri.strip())
    for child in soup_tag.contents:
        base_url += list_uris(child, uris_so_far)
    return base_url


if __name__ == '__main__':
    if len(argv) < 3:
        exit(f'Usage: python3.7 {argv[0]} html_file main_url')

    html_file: str = argv[1]
    main_url: str = argv[2]

    # throws an exception if main url does not have :
    if main_url.find(':') == -1:
        exit('Main URL should include the scheme (http/https) !')

    scheme: str = main_url[:main_url.index(':')]
    # drop the trailing /, if any
    if main_url[-1] == '/':
        main_url = main_url[:-1]

    resource_uris: List[str] = []
    with open(html_file, 'r') as html_handle:
        soup_root = parse_html(html_handle)
        list_uris(soup_root, resource_uris)

    for uri in resource_uris:
        if uri.startswith('//'):
            # inherits the main url scheme
            print(scheme+':'+uri)
        elif uri.startswith('/'):
            # relative url
            print(main_url+uri)
        elif uri.startswith('http'):
            # absolute url
            print(uri)
        elif uri.startswith('static.bhphoto.com/'):
            # making exception for bhphotovideo
            print('http://'+uri)
        elif not uri.endswith('.net') and \
                not uri.endswith('.com') and \
                not uri.endswith('.cn') and \
                not uri.startswith('”') and \
                uri != 'null' and \
                not len(uri) == 0:
            # making exceptions because of msn, audiable, jetblue, cnn
            print(main_url+'/'+uri)
