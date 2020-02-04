from os import path, listdir, getcwd, chdir
from sys import argv, exit
from typing import Set, List, Tuple, Dict
from subprocess import run
import numpy as np
import re

data_dir: str = path.abspath('../filtered-urls/data')
output = open(path.join(path.abspath('..'), 'blocked_urls.csv'), 'w')
dir_url_map: Dict[str, str] = {}

def run_command(command: str) -> Tuple[str, str]:
    completed = run(command, shell=True, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8"))

    stdout = completed.stdout.decode('utf-8')[:-1] # dropping the trailing \n
    stderr = completed.stderr.decode('utf-8')[:-1]
    return (stdout, stderr)

def replay_urls(page_dir: str, page_name: str, url: str) -> None:
    print(page_name)
    cmd: str = f'./replay-urls.sh {page_name} {url}'
    (stdout, stderr) = run_command(cmd)
    print('-'*30)

def run_adblocker(page_name: str, url:str) -> None:
    default_urls = path.join(data_dir, page_name, 'default-urls.txt')
    static_urls = path.join(data_dir, page_name, 'nopatch-urls.txt')
    chdir('../filtered-urls')
    cmd: str = f'cargo run {url} {default_urls} {static_urls}'
    (stdout, stderr) = run_command(cmd)
    lines: List[str] = stdout.split('\n')
    total: float = float(lines[0].split(':')[1])
    if total == 0:
        total = 1
    default_num: int = int(lines[1].split(':')[1])
    fawkes_num: int = int(lines[2].split(':')[1])
    print(page_name)
    output.write(f'{page_name}, {default_num}, {fawkes_num}, {(default_num/total):.2f}, {(fawkes_num/total):.2f}\n')
    print('-'*30)
    chdir('../fawkes')

################################################################################
if len(argv) < 4:
    usage: str = f'Usage: python3.7 {argv[0]} dir_urls.txt -replay pages_replay_dir'+'\n'
    usage += f'Usage: python3.7 {argv[0]} dir_urls.txt -blocker pages_replay_dir/data_dir'
    exit(usage)

with open(argv[1], 'r') as dir_urls:
    for line in dir_urls:
        parts: List[str] = line.strip().split(' ')
        dir_url_map[parts[0]] = parts[1]

option: str = argv[2]
main_dir: str = argv[3]
if not path.isdir(main_dir):
    raise ValueError('Second argument is not a directory!')

if main_dir[-1] == '/':
    main_dir = main_dir[0:-1] # remove trailing slash for basename

output.write('default, fawkes_static, default_per, fawkes_static_per\n')
dirs: List[str] = listdir(main_dir)
for page_name in dirs: # arbitrary order
    page_dir: str = path.join(main_dir, page_name)
    url: str = dir_url_map.get(page_name, "")
    if url != "" and path.isdir(page_dir):
        try:
            if option == '-replay':
                replay_urls(page_dir, page_name, url)
            else:
                run_adblocker(page_name, url)
        except RuntimeError as e:
            print(f'Skipping {page_name} -> {e}')
    # else:
    #     print(f'Some trouble with {page_name} ... {url}')

output.close()
print('Done!')

