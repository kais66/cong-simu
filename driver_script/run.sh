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

#for thisRate in "${abilene_equal_rates[@]}"; do
#    python main.py PerFlow $thisRate false > $output_sink 
#done

for thisRate in "${abilene_equal_rates[@]}"; do
    python main.py PerIf $thisRate true > $output_sink 
done
