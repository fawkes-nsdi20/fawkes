#!/bin/bash
# set -x

# our version: "../mm-recording/chrome-caching/chrome"
CHROME_PATH="/usr/bin/google-chrome"
OUT_FILE="intersected_urls.txt"

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
max_it=$2

if [[ -z $url || -z $max_it ]]; then
      echo Usage: ./common-requested-urls.sh url max_iteration
      exit 12
fi

# use the first load for initializing the intersection file
load_page $url "/tmp/nonexistent$(date +%s$i)" urls_1.txt
cp urls_1.txt "$OUT_FILE"

it=2
while [[ $it -le $max_it ]]; do
    load_page $url "/tmp/nonexistent$(date +%s$i)" "urls_$it.txt"
    # get the intersection of this new file with prev intersections
    comm -12 "$OUT_FILE" "urls_$it.txt" > temp
    # sort the result for the next iterations
    sort temp > "$OUT_FILE"
    ((it++))
done

# clean up the extra files
rm temp
rm -r urls_*.txt