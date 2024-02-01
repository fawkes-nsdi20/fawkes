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
