#!/bin/bash

source rates.sh

cong_arr=(PerFlow PerIf)
ecn='true'
cd ../


#for congStr in ${cong_arr[*]}; do
#    for thisRate in "${rates[@]}"; do
#        python main.py $congStr $thisRate false
#    done
#done

output_sink="/dev/null"

for thisRate in "${Small9AllPairEqualRates[@]}"; do
    python main.py PerIf True Small9 AllPairEqual $thisRate > $output_sink 
done
