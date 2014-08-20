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
"""This file contains a parser for MS Office MRUs for Plaso."""

import logging
import re

from plaso.lib import event
from plaso.lib import timelib
from plaso.parsers.winreg_plugins import interface


__author__ = 'David Nides (david.nides@gmail.com)'


class OfficeMRUPlugin(interface.KeyPlugin):
  """Plugin that parses Microsoft Office MRU keys."""

  NAME = 'winreg_office_mru'

  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'Microsoft Office MRU'

  REG_KEYS = [
      u'\\Software\\Microsoft\\Office\\14.0\\Word\\Place MRU',
      u'\\Software\\Microsoft\\Office\\14.0\\Access\\File MRU',
      u'\\Software\\Microsoft\\Office\\14.0\\Access\\Place MRU',
      u'\\Software\\Microsoft\\Office\\14.0\\PowerPoint\\File MRU',
      u'\\Software\\Microsoft\\Office\\14.0\\PowerPoint\\Place MRU',
      u'\\Software\\Microsoft\\Office\\14.0\\Excel\\File MRU',
      u'\\Software\\Microsoft\\Office\\14.0\\Excel\\Place MRU',
      u'\\Software\\Microsoft\\Office\\14.0\\Word\\File MRU']

  _RE_VALUE_NAME = re.compile(r'^Item [0-9]+$', re.I)

  # The Office 12 item MRU is formatted as:
  # [F00000000][T%FILETIME%]*\\%FILENAME%

  # The Office 14 item MRU is formatted as:
  # [F00000000][T%FILETIME%][O00000000]*%FILENAME%
  _RE_VALUE_DATA = re.compile(r'\[F00000000\]\[T([0-9A-Z]+)\].*\*[\\]?(.*)')

  def GetEntries(self, unused_parser_context, key=None, **unused_kwargs):
    """Collect Values under Office 2010 MRUs and return events for each one.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      key: The Registry key (instance of winreg.WinRegKey) in which the value
           is stored.
    """
    # TODO: Test other Office versions to makesure this plugin is applicable.
    for value in key.GetValues():
      # Ignore any value not in the form: 'Item [0-9]+'.
      if not value.name or not self._RE_VALUE_NAME.search(value.name):
        continue

      # Ignore any value that is empty or that does not contain a string.
      if not value.data or not value.DataIsString():
        continue

      values = self._RE_VALUE_DATA.findall(value.data)

      # Values will contain a list containing a tuple containing 2 values.
      if len(values) != 1 or len(values[0]) != 2:
        continue

      try:
        filetime = int(values[0][0], 16)
      except ValueError:
        logging.warning('Unable to convert filetime string to an integer.')
        filetime = 0

      # TODO: why this behavior? Only the first Item is stored with its
      # timestamp. Shouldn't this be: Store all the Item # values with
      # their timestamp and store the entire MRU as one event with the
      # registry key last written time?
      if value.name == 'Item 1':
        timestamp = timelib.Timestamp.FromFiletime(filetime)
      else:
        timestamp = 0

      text_dict = {}
      text_dict[value.name] = value.data

      yield event.WinRegistryEvent(
          key.path, text_dict, timestamp=timestamp,
          source_append=': {0:s}'.format(self.DESCRIPTION))
