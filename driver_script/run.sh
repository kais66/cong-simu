#!/bin/bash

# usage: ./run.sh exp_str use_ECN
# example: ./run.sh PerIf True
exp_str=$1
use_ECN=$2

source rates.sh

cd ../


#for congStr in ${cong_arr[*]}; do
#    for thisRate in "${rates[@]}"; do
#        python main.py $congStr $thisRate false
#    done
#done

output_sink="/dev/null"

#for thisRate in "${Small9SkewedRates[@]}"; do
#    python main.py $exp_str $use_ECN Small9 Skewed $thisRate > $output_sink 
#done

for thisRate in "${AbileneEqualRates[@]}"; do
    echo "running rate: $thisRate"
    python main.py $exp_str $use_ECN Abilene Equal $thisRate > $output_sink 
done
