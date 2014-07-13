#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Formatter for the Windows events."""

from plaso.formatters import interface


class WindowsVolumeCreationEventFormatter(interface.ConditionalEventFormatter):
  """Class that formats Windows volume creation events."""

  DATA_TYPE = 'windows:volume:creation'

  FORMAT_STRING_PIECES = [
      u'{device_path}',
      u'Serial number: 0x{serial_number:08X}',
      u'Origin: {origin}']

  FORMAT_STRING_SHORT_PIECES = [
      u'{device_path}',
      u'Origin: {origin}']

  SOURCE_LONG = 'System'
  SOURCE_SHORT = 'LOG'
