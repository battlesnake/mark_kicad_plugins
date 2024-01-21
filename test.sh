#!/bin/bash

# Set CPU #2 to fixed speed and run with high realtime priority on it

declare cpu=/sys/devices/system/cpu/cpufreq/policy2
declare speed=2200000

echo "$speed" | sudo tee "$cpu/scaling_min_freq" >/dev/null
echo "$speed" | sudo tee "$cpu/scaling_max_freq" >/dev/null

sudo nice -n -10 chrt -r 99 taskset -ac 2 python -m self
echo "Exit-code: $?"

cat "$cpu/cpuinfo_min_freq" | sudo tee "$cpu/scaling_min_freq" >/dev/null
cat "$cpu/cpuinfo_max_freq" | sudo tee "$cpu/scaling_max_freq" >/dev/null
