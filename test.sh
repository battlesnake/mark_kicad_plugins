#!/bin/bash

set -xeu

cd "$(dirname "$0")/.."
exec python -m mark_kicad_plugins
