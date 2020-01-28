#!/bin/bash
# set -x

# CHROME_PATH="/usr/bin/google-chrome"
CHROME_PATH="../../mm-recording/chrome-caching/chrome"
OUT_FILE="urls.txt"

load_page () {
    # Start our own version of chrome with the given user-data-dir
    # and output_file to save the requested urls
    # $1 -> url
    # $2 -> user-data-dir for chrome
    # $3 -> output_path
    url=$1
    chrome_user_data_dir=$2
    out_path=$3
    "$CHROME_PATH" \
        --remote-debugging-port=9222 \
        --disable-logging \
        --disable-default-apps \
        --enable-benchmarking \
        --enable-net-benchmarking \
        --headless \
        --ignore-certificate-errors \
        --no-check-certificate \
        --no-default-browser-check \
        --no-first-run \
        --user-data-dir=$chrome_user_data_dir &

    process_id=`/bin/ps -fu $USER| grep "chrome --remote-debugging-port=9222" | grep -v "grep" | awk '{print $2}'`
    sleep 5
    timeout 300 node chrome-urls.js $url | sort > $out_path
    sleep 15
    kill -9 $process_id
    sleep 5
}

url=$1
if [[ -z $url ]]; then
      echo Usage: ./all-urls.sh url
      exit 12
fi

if [[ ! -z "$2" ]]; then
    OUT_FILE=$2
fi

# load the page to record all the requested urls on network
load_page $url "/tmp/nonexistent$(date +%s$N)" "$OUT_FILE"
