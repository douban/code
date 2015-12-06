#!/bin/bash -ex

dae venv python -- -m pylint.lint $*
