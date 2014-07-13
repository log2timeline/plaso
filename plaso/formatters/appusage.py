#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""This file contains a formatter for the Mac OS X application usage."""

from plaso.formatters import interface


class ApplicationUsageFormatter(interface.EventFormatter):
  """Define the formatting for Application Usage information."""

  DATA_TYPE = 'macosx:application_usage'

  FORMAT_STRING = (u'{application} v.{app_version} (bundle: {bundle_id}).'
                   ' Launched: {count} time(s)')
  FORMAT_STRING_SHORT = u'{application} ({count} time(s))'

  SOURCE_LONG = 'Application Usage'
  SOURCE_SHORT = 'LOG'
