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

#! /bin/bash

page_name=$1
url=$2

if [[ -z $page_name || -z $url ]]; then
    echo 'Usage: ./run-chrome.sh page_name url'
    exit 12
fi

new_user_dir="/tmp/$page_name$(date +%s%N)"

./chrome-caching/chrome \
    --user-data-dir="$new_user_dir" \
    --remote-debugging-port=9222 \
    --allow-insecure-localhost \
    --disable-logging \
    --disable-default-apps \
    --enable-benchmarking \
    --enable-net-benchmarking \
    --headless \
    --ignore-certificate-errors \
    --no-check-certificate \
    --no-default-browser-check \
    --no-first-run &

sleep 5
process_id=`/bin/ps -fu $USER | grep -e "--user-data-dir=$new_user_dir" | grep -v 'grep' | awk '{print $2}'`
timeout 300 node chrome.js about:blank
sleep 1
timeout 300 node chrome.js $url
sleep 10
# In case process_id is not only one id, which should not happen
echo $process_id | xargs kill -9
sleep 5
