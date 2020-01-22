#! /bin/bash
set -x

url=$1
case_name=$2

yarn pwmetrics $url --config=pwconfig.js $case_name cold
#for i in {1..5}
#do
#    ./mymahimahi.sh /tmp/nonexistent$(date +%s%N) > out/$case_name/cold\_$i.log
#done

id=$(date +%s%N)
yarn pwmetrics $url --config=pwconfig.js $case_name\_$id
yarn pwmetrics $url --config=pwconfig.js $case_name\_$id warm

#./mymahimahi.sh /tmp/mm\_$case_name\_PLT\_$id > /dev/null
#for i in {1..5}
#do
#    ./mymahimahi.sh /tmp/mm\_$case_name\_PLT\_$id > out/$case_name/warm\_$i.log
#done
