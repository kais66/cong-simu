#!/bin/bash

cd ../
#for (( i=2000; i<15000; i=i+1000)); do
for (( i=2000; i<30000; i=i+1000)); do
    python ./demand.py $i
done
