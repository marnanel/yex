#!/bin/bash

sphinx-apidoc -f -o docs/source yex
cd docs
make html
