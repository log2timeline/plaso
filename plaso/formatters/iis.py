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
"""Formatter for Windows IIS log files."""

from plaso.formatters import interface


__author__ = 'Ashley Holtz (ashley.a.holtz@gmail.com)'


class WinIISFormatter(interface.ConditionalEventFormatter):
  """A formatter for Windows IIS log entries."""

  DATA_TYPE = 'iis:log:line'

  FORMAT_STRING_PIECES = [
      u'{http_method}',
      u'{requested_uri_stem}',
      u'[',
      u'{source_ip}',
      u'>',
      u'{dest_ip}',
      u':',
      u'{dest_port}',
      u']',
      u'Http Status: {http_status}',
      u'Bytes Sent: {sent_bytes}',
      u'Bytes Received: {received_bytes}',
      u'User Agent: {user_agent}',
      u'Protocol Version: {protocol_version}',]

  FORMAT_STRING_SHORT_PIECES = [
      u'{http_method}',
      u'{requested_uri_stem}',
      u'[',
      u'{source_ip}',
      u'>',
      u'{dest_ip}',
      u':',
      u'{dest_port}',
      u']',]

  SOURCE_LONG = 'IIS Log'
  SOURCE_SHORT = 'LOG'
