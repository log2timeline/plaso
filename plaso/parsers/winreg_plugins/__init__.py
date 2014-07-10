#!/usr/bin/python
# -*- coding: utf-8 -*-
#
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
"""This file contains the import statements for the Registry plugins."""

from plaso.parsers.winreg_plugins import appcompatcache
from plaso.parsers.winreg_plugins import ccleaner
from plaso.parsers.winreg_plugins import default
from plaso.parsers.winreg_plugins import lfu
from plaso.parsers.winreg_plugins import mountpoints
from plaso.parsers.winreg_plugins import mrulist
from plaso.parsers.winreg_plugins import mrulistex
from plaso.parsers.winreg_plugins import msie_zones
from plaso.parsers.winreg_plugins import officemru
from plaso.parsers.winreg_plugins import outlook
from plaso.parsers.winreg_plugins import run
from plaso.parsers.winreg_plugins import services
from plaso.parsers.winreg_plugins import task_scheduler
from plaso.parsers.winreg_plugins import terminal_server
from plaso.parsers.winreg_plugins import typedurls
from plaso.parsers.winreg_plugins import userassist
from plaso.parsers.winreg_plugins import usbstor
from plaso.parsers.winreg_plugins import winrar
from plaso.parsers.winreg_plugins import winver
