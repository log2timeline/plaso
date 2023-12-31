#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Installation and deployment script."""

import glob
import os

from setuptools import setup


setup(
    data_files=[
        ('share/plaso', glob.glob(os.path.join('data', '*.*'))),
        ('share/plaso/formatters', glob.glob(os.path.join(
            'data', 'formatters', '*.yaml')))])
