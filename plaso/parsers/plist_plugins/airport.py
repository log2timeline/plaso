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
"""This file contains the airport plist plugin in Plaso."""

from plaso.events import plist_event
from plaso.lib import timelib
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class AirportPlugin(interface.PlistPlugin):
  """Plist plugin that extracts WiFi information."""

  NAME = 'plist_airport'

  PLIST_PATH = 'com.apple.airport.preferences.plist'
  PLIST_KEYS = frozenset(['RememberedNetworks'])

  def GetEntries(self, match, **unused_kwargs):
    """Extracts relevant Airport entries.

    Args:
      match: A dictionary containing keys extracted from PLIST_KEYS.

    Yields:
      EventObject objects extracted from the plist.
    """
    for wifi in match['RememberedNetworks']:
      time = timelib.Timestamp.FromPythonDatetime(
          wifi['LastConnected'])
      description = (
          u'[WiFi] Connected to network: <{}> '
          u'using security {}').format(
              wifi['SSIDString'], wifi['SecurityType'])
      yield plist_event.PlistEvent(
          u'/RememberedNetworks', u'item', time, description)

