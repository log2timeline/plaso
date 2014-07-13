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
"""Formatter for the iPod device events."""

from plaso.formatters import interface


class IPodDeviceFormatter(interface.ConditionalEventFormatter):
  """Formatter for iPod device events."""

  DATA_TYPE = 'ipod:device:entry'

  FORMAT_STRING_PIECES = [
      u'Device ID: {device_id}',
      u'Type: {device_class}',
      u'[{family_id}]',
      u'Connected {use_count} times',
      u'Serial nr: {serial_number}',
      u'IMEI [{imei}]']

  SOURCE_LONG = 'iPod Connections'
  SOURCE_SHORT = 'LOG'
