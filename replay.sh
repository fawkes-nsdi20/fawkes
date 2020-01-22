#! /bin/bash

dir_path=$1
echo Replaying $dir_path

mm-webreplay $dir_path \
mm-link ../mahimahi/traces/Verizon-LTE-short.up ../mahimahi/traces/Verizon-LTE-short.down \
mm-delay 50
