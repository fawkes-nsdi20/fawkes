import sys, os, logging
from typing import Dict
from subprocess import run
from datetime import datetime

OUT_DIR: str = 'pages'

def record_page(page_name: str, url: str, time: str) -> None:
    print(f'Started recording page: {page_name} -> {url}')
    page_dir = os.path.join(OUT_DIR, page_name)
    if not os.path.isdir(page_dir):
        created = run(f'mkdir -p {page_dir}', shell=True)
        if created.returncode != 0:
            print(f'[{page_name}] Failed to mkdir outer directory.')
            return

    case: str = page_name+'-'+time
    case_dir = os.path.join(page_dir, case)
    if os.path.isdir(case_dir): # case_dir should not exist before
        print(f'[{page_name}] Failed to mkdir {case_dir}, it already exists.')
        return

    webrecord_cmd: str = f'mm-webrecord {case_dir} ./run-chrome.sh {case} {url}'
    recorded = run(webrecord_cmd, shell=True)
    if recorded.returncode != 0:
        print(f'[{page_name}] Failed to record: {str(recorded)}')
    else:
        print(f'[{page_name}] Recording completed > {case}')


def get_page_name(url: str) -> str:
    from urllib.parse import urlparse, ParseResult
    page_name: str = ''
    try:
        parsed_url: ParseResult = urlparse(url)
        domain: str = parsed_url.netloc
        if domain.startswith('www.'): # remove 'www.' if exists
            domain = domain[4:]
        last_dot = domain.rindex('.') # find last index of '.'
        domain = domain[:last_dot] # remove the last part of url e.g. com/gov/..
        page_name = domain.replace('.', '_') # replace the sub-domain dots with _
    except e:
        print(f'[get_page_name] Raised some exception while parsing {url}')
    finally:
        return page_name

def read_alexa_file(alexa_file_path: str) -> Dict[str, str]:
    all_pages: Dict[str, str] = {}
    with open(alexa_file_path, 'r') as alexa:
        for line in alexa:
            if not line.startswith('#'): # ignore comments in the file
                url: str = line.strip()
                page_name: str = get_page_name(url)
                if page_name != '': # ignore the url if it was not parse-able
                    if all_pages.get(page_name) != None: # duplicate entry in the alexa file
                        print(f'[main] Duplicate entry {url} vs. {all_pages.get(page_name)}.')
                    else:
                        all_pages[page_name] = url
                else:
                    print(f'[main] Ignored {url} due to an error while parsing the page name.')
    return all_pages

def read_page_urls_file(page_urls_path: str) -> Dict[str, str]:
    all_pages: Dict[str, str] = {}
    with open(page_urls_path, 'r') as input_f:
        for line in input_f:
            parts: List[str] = line.strip().split(' ')
            all_pages[parts[0]] = parts[1]
    return all_pages

if __name__ == '__main__':

    if len(sys.argv) < 2:
        sys.exit('Usage: python3.7 record_all.py urls_file [twice_or_not]')

    file_path: str = sys.argv[1]
    record_twice: bool = False
    if len(sys.argv) > 2 and sys.argv[2] != 'False':
        record_twice = True

    # all_pages: Dict[str, str] = read_alexa_file(file_path)
    all_pages: Dict[str, str] = read_page_urls_file(file_path)

    time_tag: str = datetime.now().strftime('%Y-%m-%dT%H-%M')
    for (page, url) in all_pages.items():
        if url[-1] != '/':
            url += '/'
        record_page(page, url, time_tag)
        if record_twice:
            # call the recorder another time if you want back-to-back
            record_page(page, url, time_tag+'-b2b')



