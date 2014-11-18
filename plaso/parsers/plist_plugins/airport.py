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
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class AirportPlugin(interface.PlistPlugin):
  """Plist plugin that extracts WiFi information."""

  NAME = 'plist_airport'
  DESCRIPTION = u'Parser for Airport plist files.'

  PLIST_PATH = 'com.apple.airport.preferences.plist'
  PLIST_KEYS = frozenset(['RememberedNetworks'])

  def GetEntries(
      self, parser_context, file_entry=None, parser_chain=None, match=None,
      **unused_kwargs):
    """Extracts relevant Airport entries.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: Optional file entry object (instance of dfvfs.FileEntry).
                  The default is None.
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
      match: Optional dictionary containing keys extracted from PLIST_KEYS.
             The default is None.
    """
    for wifi in match['RememberedNetworks']:
      description = (
          u'[WiFi] Connected to network: <{0:s}> using security {1:s}').format(
              wifi['SSIDString'], wifi['SecurityType'])
      event_object = plist_event.PlistEvent(
          u'/RememberedNetworks', u'item', wifi['LastConnected'], description)
      parser_context.ProduceEvent(
          event_object, parser_chain=parser_chain, file_entry=file_entry)


plist.PlistParser.RegisterPlugin(AirportPlugin)
