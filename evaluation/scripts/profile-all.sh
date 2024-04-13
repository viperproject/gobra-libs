#!/bin/bash

# This file is part of gobra-libs which is released under the MIT license.
# See LICENSE or go to https://github.com/viperproject/gobra-libs/blob/main/LICENSE
# for full license details.

# In case you are using a laptop, make sure that power settings are set
# properly:
# - don't run from battery
# - make sure the correct profile is set, i.e. not the battery profile
#   (e.g., in TLP)
# - make sure the laptop will not suspend
#   - check packages that may interfere
#   - use systemd-inhibit

ITERATIONS=30

# Set the path to silicon.sh
SILICON_PATH=
# Set the path to the Z3 binary
# Tested Versions: 4.8.7 (newer versions may not work; produce errors and different output) 
Z3_PATH=
# Set the path to the Gobra jar
GOBRA_PATH=

# profile with disabled set axioms
python profile.py ../experiments/synthetic_set/fully_assisted/fully_assisted.gobra --disableSetAxiomatization --z3RandomizeSeeds --iterations $ITERATIONS --silicon_path $SILICON_PATH --z3_path $Z3_PATH --gobra $GOBRA_PATH

# profile all files "normally"
find ../experiments -type f -name "*.gobra" -exec python profile.py {} --z3RandomizeSeeds --iterations $ITERATIONS --silicon_path $SILICON_PATH --z3_path $Z3_PATH --gobra $GOBRA_PATH \;

# generate plots for every csv
find ../experiments -type f -name "*.csv" -exec python plot.py --qi_size 9 9 {} \;
