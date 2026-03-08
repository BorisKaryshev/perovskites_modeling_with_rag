#!/bin/bash

set -eou pipefail
set -x

find . -name __pycache__ -type d | xargs rm -rf
