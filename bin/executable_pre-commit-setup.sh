#!/usr/bin/bash

ln -s ~/git/global_venv/.pre-commit-config.yaml .pre-commit-config.yaml
pre-commit install
