#!/bin/bash

cong_str='PerFlow'
#cong_str='PerIf'

cong_arr=(PerFlow PerIf)
cd ../
for x in ${cong_arr[*]}; do
    for (( i=2000; i<9000; i=i+1000)); do
        python main.py $x $i
        #echo "cong_str: $x, rate_str: $i"
    done
done

