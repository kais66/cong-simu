#!/bin/bash

#cong_str='PerFlow'
cong_str='PerIf'

cong_arr=(PerFlow PerIf)
ecn='true'
cd ../

#for x in ${cong_arr[*]}; do
    #for (( i=2000; i<20000; i=i+1000)); do
#    for (( i=2000; i<20000; i=i+2000)); do
#        python main.py $x $i false 
#    done
#done

for (( i=2000; i<16000; i=i+2000)); do
  #python main.py PerIf $i true
  python main.py PerFlow $i
done

