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
