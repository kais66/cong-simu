#!/bin/bash

# demand_str can be any of the following:
# SmallEqual, SmallSkewed, RawSprint

source rates.sh

cd ../
#for (( i=2000; i<30000; i=i+1000)); do
#    python ./demand.py $i
#done

for thisRate in "${Level3EqualRates[@]}"; do
    python ./gen_traffic.py Level3 Equal $thisRate
done
