#!/bin/bash

set -xeu

cd "$(dirname "$0")/.."
exec taskset -c 2 python -m mark_kicad_plugins
