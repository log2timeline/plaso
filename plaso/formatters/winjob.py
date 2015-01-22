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
"""Formatter for Windows Scheduled Task job events."""

from plaso.formatters import interface
from plaso.formatters import manager


class WinJobFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Java Cache IDX download item."""

  DATA_TYPE = 'windows:tasks:job'

  FORMAT_STRING_PIECES = [
      u'Application: {application}',
      u'{parameter}',
      u'Scheduled by: {username}',
      u'Working Directory: {working_dir}',
      u'Run Iteration: {trigger}']

  SOURCE_LONG = 'Windows Scheduled Task Job'
  SOURCE_SHORT = 'JOB'


manager.FormattersManager.RegisterFormatter(WinJobFormatter)
