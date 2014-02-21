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
"""This file contains the Spotlight Volume Configuration plist in Plaso."""

from plaso.events import plist_event
from plaso.lib import timelib
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class SpotlightVolumePlugin(interface.PlistPlugin):
  """Basic plugin to extract the Spotlight Volume Configuration."""

  NAME = 'plist_spotligth_volume'

  PLIST_PATH = 'VolumeConfiguration.plist'
  PLIST_KEYS = frozenset(['Stores'])

  def GetEntries(self, match, **unused_kwargs):
    """Extracts relevant VolumeConfiguration Spotlight entries.

    Args:
      match: A dictionary containing keys extracted from PLIST_KEYS.

    Yields:
      EventObject objects extracted from the plist.
    """
    for volume_name, volume in match['Stores'].iteritems():
      time = timelib.Timestamp.FromPythonDatetime(
          volume['CreationDate'])
      description = u'Spotlight Volume {} ({}) activated.'.format(
          volume_name, volume['PartialPath'])
      yield plist_event.PlistEvent(
          u'/Stores', '', time, description)

