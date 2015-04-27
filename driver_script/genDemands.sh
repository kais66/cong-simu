#!/bin/bash

cd ../
for (( i=2000; i<9000; i=i+1000)); do
    python ./demand.py $i
done
