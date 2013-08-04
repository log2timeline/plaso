#!/usr/bin/python
# -*- coding: utf-8 -*-
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

from plaso.lib import event
from plaso.lib import timelib
from plaso.lib import win_registry_interface


__author__ = 'David Nides (david.nides@gmail.com)'


class OfficeMRU(win_registry_interface.KeyPlugin):
  """Base class for all Office 2010 MRU plugins."""

  __abstract = True

  DESCRIPTION = 'Office MRU'

  def GetTimeStamp(self, stringdata):
    """Get timestamp from string data."""
    if len(stringdata) >= 29:
      try:
        # Get Timestamp from string.
        datetime = stringdata[13:29]
        return timelib.Timestamp.FromFiletime(int(datetime, 16))
      except ValueError:
        logging.warning('Datetime value not correct')
        return 0

  def GetEntries(self):
    """Collect Values under Office 2010 MRUs and return events for each one."""
    # TODO: Test other Office versions to makesure this plugin is applicable.
    for value in self._key.GetValues():
      if not value.name:
        continue

      # TODO: Registry refactor, replace GetStringData().
      stringdata = value.GetStringData()

      if not stringdata.startswith('[F00000000'):
        continue

      text_dict = {}
      text_dict[value.name] = stringdata

      if value.name == 'Item 1':
        reg_evt = event.WinRegistryEvent(
            self._key.path, text_dict,
            timestamp=self.GetTimeStamp(stringdata))
      else:
        reg_evt = event.WinRegistryEvent(
            self._key.path, text_dict, timestamp=0)

      reg_evt.source_append = ': {}'.format(self.DESCRIPTION)
      yield reg_evt


# TODO: Address different MS Office versions.
class MSWord2010PlaceMRU(OfficeMRU):
  """Gathers the MS Word Place 2010 MRU keys for the NTUSER hive."""

  REG_KEY = '\\Software\\Microsoft\\Office\\14.0\\Word\\Place MRU'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'Word Place MRU'


class MSWord2010FileMRU(OfficeMRU):
  """Gathers the MS Word File 2010 MRU keys for the NTUSER hive."""

  REG_KEY = '\\Software\\Microsoft\\Office\\14.0\\Word\\File MRU'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'Word File MRU'


class MSExcel2010PlaceMRU(OfficeMRU):
  """Gathers the MS Excel 2010 Place MRU keys for the NTUSER hive."""

  REG_KEY = '\\Software\\Microsoft\\Office\\14.0\\Excel\\Place MRU'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'Excel Place MRU'


class MSExcel2010FileMRU(OfficeMRU):
  """Gathers the MS Excel 2010 File MRU keys for the NTUSER hive."""

  REG_KEY = '\\Software\\Microsoft\\Office\\14.0\\Excel\\File MRU'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'Excel File MRU'


class MSPowerPoint2010PlaceMRU(OfficeMRU):
  """Gathers the MS PowerPoint Place 2010 MRU keys for the NTUSER hive."""

  REG_KEY = '\\Software\\Microsoft\\Office\\14.0\\PowerPoint\\Place MRU'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'PowerPoint Place MRU'


class MSPowerPoint2010FileMRU(OfficeMRU):
  """Gathers the MS PowerPoint File 2010 MRU keys for the NTUSER hive."""

  REG_KEY = '\\Software\\Microsoft\\Office\\14.0\\PowerPoint\\File MRU'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'PowerPoint File MRU'


class MSAccess2010PlaceMRU(OfficeMRU):
  """Gathers the MS Access Place 2010 MRU keys for the NTUSER hive."""

  REG_KEY = '\\Software\\Microsoft\\Office\\14.0\\Access\\Place MRU'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'Access Place MRU'


class MSAccess2010FileMRU(OfficeMRU):
  """Gathers the MS Access File 2010 MRU keys for the NTUSER hive."""

  REG_KEY = '\\Software\\Microsoft\\Office\\14.0\\Access\\File MRU'
  REG_TYPE = 'NTUSER'
  DESCRIPTION = 'Access File MRU'
