#!/usr/bin/env bash

cd /root/luma
# Init database and start LUMA server
./init_db.py
./main.py -gm generators_mapping.json