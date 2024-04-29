#!/bin/bash

# This file is part of gobra-libs which is released under the MIT license.
# See LICENSE or go to https://github.com/viperproject/gobra-libs/blob/main/LICENSE
# for full license details.

# DEPENDENCIES (plot.py):
# - pandas
# - numpy
# - seaborn
# - matplotlib
# In case you forgot to install the dependencies before running the script, you
# do not need to rerun this script (and in particular profiling); instead, simply use
# the command for plotting found below.

# USAGE:
# First, make sure the following variables are set:
# - SILICON_PATH (should contain path to silicon.sh)
# - Z3_PATH (should contain path to the Z3 binary)
# - GOBRA_PATH (should contain path to Gobra jar)
# Note that we only tested Z3 4.8.7; newer versions may not work as
# they produce errors and different output.
#
# Finally, switch into the same directory as profile-all.sh, and run the script.
#
# In case you are using a laptop, make sure that power settings are set
# properly:
# - don't run from battery
# - make sure the correct profile is set, i.e. not the battery profile
#   (e.g., in TLP)
# - make sure the laptop will not suspend
#   - check packages that may interfere
#   - use systemd-inhibit

ITERATIONS=30

# Check if the environment variables are unset or empty
if [ -z "$SILICON_PATH" ]; then
    echo "Please set the environment variable SILICON_PATH to the path to silicon.sh."
    exit 1
fi
if [ -z "$Z3_PATH" ]; then
    echo "Please set the environment variable Z3_PATH to the path to the Z3 binary."
    exit 1
fi
if [ -z "$GOBRA_PATH" ]; then
    echo "Please set the environment variable GOBRA_PATH to the path to the Gobra jar."
    exit 1
fi

# profile with disabled set axioms
python3 profile.py ../experiments/synthetic_set/fully_assisted/fully_assisted.gobra --disableSetAxiomatization --z3RandomizeSeeds --iterations $ITERATIONS --silicon_path $SILICON_PATH --z3_path $Z3_PATH --gobra $GOBRA_PATH

# profile all files "normally"
find ../experiments -type f -name "*.gobra" -exec python3 profile.py {} --z3RandomizeSeeds --iterations $ITERATIONS --silicon_path $SILICON_PATH --z3_path $Z3_PATH --gobra $GOBRA_PATH \;

# generate plots for every csv
find ../experiments -type f -name "*.csv" -exec python3 plot.py --qi_size 9 9 {} \;
