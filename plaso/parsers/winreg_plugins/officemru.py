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


class OfficeMRU(interface.KeyPlugin):
  """Base class for all Office 2010 MRU plugins."""

  # TODO: Re-enable after we modify the key plugin so that it can define more
  # than a single registry key.
  #NAME = 'winreg_office_mru'

  __abstract = True

  DESCRIPTION = 'Office MRU'

  _RE_VALUE_NAME = re.compile(r'^Item [0-9]+$', re.I)

  # The Office 12 item MRU is formatted as:
  # [F00000000][T%FILETIME%]*\\%FILENAME%

  # The Office 14 item MRU is formatted as:
  # [F00000000][T%FILETIME%][O00000000]*%FILENAME%
  _RE_VALUE_DATA = re.compile(r'\[F00000000\]\[T([0-9A-Z]+)\].*\*[\\]?(.*)')

  def GetEntries(self):
    """Collect Values under Office 2010 MRUs and return events for each one."""
    # TODO: Test other Office versions to makesure this plugin is applicable.
    for value in self._key.GetValues():
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
          self._key.path, text_dict, timestamp=timestamp,
          source_append=': {0:s}'.format(self.DESCRIPTION))


# TODO: Address different MS Office versions.
# TODO: Remove these classes and merge into a single one once the key plugin has
# been changed to accomodate lists of registry keys.
class MSWord2010PlaceMRU(OfficeMRU):
  """Gathers the MS Word Place 2010 MRU keys for the User hive."""

  NAME = 'winreg_msword_2012_place'

  REG_KEY = '\\Software\\Microsoft\\Office\\14.0\\Word\\Place MRU'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'Word Place MRU'


class MSWord2010FileMRU(OfficeMRU):
  """Gathers the MS Word File 2010 MRU keys for the User hive."""

  NAME = 'winreg_msword_2010_file'

  REG_KEY = '\\Software\\Microsoft\\Office\\14.0\\Word\\File MRU'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'Word File MRU'


class MSExcel2010PlaceMRU(OfficeMRU):
  """Gathers the MS Excel 2010 Place MRU keys for the User hive."""

  NAME = 'winreg_msexcel_place'

  REG_KEY = '\\Software\\Microsoft\\Office\\14.0\\Excel\\Place MRU'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'Excel Place MRU'


class MSExcel2010FileMRU(OfficeMRU):
  """Gathers the MS Excel 2010 File MRU keys for the User hive."""

  NAME = 'winreg_msexcel_file'

  REG_KEY = '\\Software\\Microsoft\\Office\\14.0\\Excel\\File MRU'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'Excel File MRU'


class MSPowerPoint2010PlaceMRU(OfficeMRU):
  """Gathers the MS PowerPoint Place 2010 MRU keys for the User hive."""

  NAME = 'winreg_msppt_place'

  REG_KEY = '\\Software\\Microsoft\\Office\\14.0\\PowerPoint\\Place MRU'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'PowerPoint Place MRU'


class MSPowerPoint2010FileMRU(OfficeMRU):
  """Gathers the MS PowerPoint File 2010 MRU keys for the User hive."""

  NAME = 'winreg_msppt_file'

  REG_KEY = '\\Software\\Microsoft\\Office\\14.0\\PowerPoint\\File MRU'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'PowerPoint File MRU'


class MSAccess2010PlaceMRU(OfficeMRU):
  """Gathers the MS Access Place 2010 MRU keys for the User hive."""

  NAME = 'winreg_msacc_place'

  REG_KEY = '\\Software\\Microsoft\\Office\\14.0\\Access\\Place MRU'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'Access Place MRU'


class MSAccess2010FileMRU(OfficeMRU):
  """Gathers the MS Access File 2010 MRU keys for the User hive."""

  NAME = 'winreg_msacc_file'

  REG_KEY = '\\Software\\Microsoft\\Office\\14.0\\Access\\File MRU'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'Access File MRU'
