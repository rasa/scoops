#!/usr/bin/env bash

for i in *.json; do
    python jsonfmt.py "$i"
done
