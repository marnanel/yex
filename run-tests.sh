#!/bin/bash
PYTHONPATH=. python -m pytest --log-level=WARN -s $*
