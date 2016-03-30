#!/usr/bin/env bash

cd /root/luma

# Use example configs
cp example_config/config.cfg.example config.cfg
cp example_config/generators_mapping.json.example generators_mapping.json
cp generators/generators.cfg.example generators/generators.cfg

# Init database and start LUMA server
./init_db.py
./main.py -gm generators_mapping.json