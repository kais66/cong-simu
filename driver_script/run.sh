#!/bin/bash

#cong_str='PerFlow'
cong_str='PerIf'

rates=("0.5" "0.7" "0.9" "1.1" "1.3" "1.5")

cong_arr=(PerFlow PerIf)
ecn='true'
cd ../

#for x in ${cong_arr[*]}; do
    #for (( i=2000; i<20000; i=i+1000)); do
#    for (( i=2000; i<20000; i=i+2000)); do
#        python main.py $x $i false 
#    done
#done


for congStr in ${cong_arr[*]}; do
    for thisRate in "${rates[@]}"; do
        python main.py $congStr $thisRate false
    done
done
