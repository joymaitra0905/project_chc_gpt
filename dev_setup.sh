#!/bin/bash
cd "$(dirname "$0")"

pip install -e . --user
pip install -r requirements.txt --user
