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
"""This file contains a skydrivelogerr formatter in plaso."""

from plaso.formatters import interface


class SkyDriveLogErrorFormatter(interface.ConditionalEventFormatter):
  """Formatter for SkyDrive log error files events."""

  DATA_TYPE = 'skydrive:error:line'

  FORMAT_STRING_PIECES = [
      u'[{module}',
      u'{source_code}]',
      u'{text}',
      u'({detail})']

  FORMAT_STRING_SHORT_PIECES = [u'{text}']

  SOURCE_LONG = 'SkyDrive Error Log File'
  SOURCE_SHORT = 'LOG'
