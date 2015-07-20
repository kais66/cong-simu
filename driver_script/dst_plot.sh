#!/bin/bash

#rates=("0.5" "0.7" "0.9" "1.1" "1.3" "1.5" "2.0")

# small skewed traffic
rates=("0.5" "0.7" "0.9" "1.1" "1.3" "1.5" "1.7" "2.0")

cd /Users/SunnySky/workspace/
#for (( i=2000; i<30000; i=i+1000)); do
#    python ./demand.py $i
#done

for thisRate in "${rates[@]}"; do
    python -m cong-simu.plot.dst_thru $thisRate
done
