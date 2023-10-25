#!/bin/sh

# Create directory for NaMi `.xlsx` export files.
mkdir -p ../data/in

# Create new virtual environment for python, if not already done.
[ -d ../.venv ] || python3 -m virtualenv ../.venv

# Install python dependencies.
../.venv/bin/pip3 install -r ../requirements.txt
