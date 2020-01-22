import sys, os
from subprocess import check_output, run
from subprocess import CalledProcessError

def run_command(command: str) -> str:
    completed = run(command, shell=True, capture_output=True)
    return completed.stdout[:-1].decode('utf-8')

# This file needs to be placed next to findcacheable, removeheader, changeheader  binary files.
if len(sys.argv) < 2:
    print('Usage: python3.7 update_cacheables.py directory [main_file_path]')
    sys.exit(1)

mm_tools_path = os.path.dirname(os.path.abspath(sys.argv[0]))
dir_path = sys.argv[1]
# ensure dir_path ends with a '/' as expected by findcacheable
if dir_path[-1] != '/':
    dir_path += '/'

# finds cacheable pairs of request/responses in a recorded mahimahi folder
cacheable_files = run_command(f'{mm_tools_path}/findcacheable {dir_path}')

if len(sys.argv) > 2:
    main_file_path = sys.argv[2]
    cacheable_files += '\n'+main_file_path+' main_file'

# for those which are cacheable, remove existing caching headers
# such as Cache-Control, Expires, Last-Modified
# instead add a cache-control header indicating max-age=1year
for file_info in cacheable_files.split('\n'):
    try:
        file_path = file_info.split(' ')[0]
        if(file_path != ''):
            run_command(f"{mm_tools_path}/removeheader {file_path} Expires")
            run_command(f"{mm_tools_path}/removeheader {file_path} Date")
            run_command(f"{mm_tools_path}/removeheader {file_path} Last-Modified")
            run_command(f"{mm_tools_path}/removeheader {file_path} Age")
            run_command(f"{mm_tools_path}/changeheader {file_path} Cache-Control public,max-age=31536000") # 1 year
            print(f"Updated {file_path} caching headers")
    except CalledProcessError as err:
        print(f"Failed running the command {err.cmd} -> {err.output.decode('utf-8')}")
