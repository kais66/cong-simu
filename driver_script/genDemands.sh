#!/bin/bash

# demand_str can be any of the following:
# SmallEqual, SmallSkewed, RawSprint

small_equal_rates=("0.5" "0.7" "0.9" "1.1" "1.3" "1.5" "2.0")

# small skewed traffic
small_skewed_rates=("0.5" "0.7" "0.9" "1.1" "1.3" "1.5" "1.7" "2.0")

# raw sprint traffic
raw_sprint_rates=()

cd ../
#for (( i=2000; i<30000; i=i+1000)); do
#    python ./demand.py $i
#done

for thisRate in "${rates[@]}"; do
    python ./gen_traffic.py $thisRate
done
