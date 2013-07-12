#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains an import statement for each registry related plugin."""

from plaso.registry import default
from plaso.registry import ietypedurls
from plaso.registry import internetsettings
from plaso.registry import lfu
from plaso.registry import mru
from plaso.registry import mrux
from plaso.registry import officemru
from plaso.registry import outlook
from plaso.registry import run
from plaso.registry import services
from plaso.registry import typedpaths
from plaso.registry import typedurls
from plaso.registry import win7userassist
from plaso.registry import winrar
from plaso.registry import winver
from plaso.registry import xpuserassist
