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
"""This file contains a default plist plugin in Plaso."""

from plaso.events import plist_event
from plaso.lib import timelib
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class SoftwareUpdatePlugin(interface.PlistPlugin):
  """Basic plugin to extract the Mac OS X update status."""

  NAME = 'plist_softwareupdate'

  PLIST_PATH = 'com.apple.SoftwareUpdate.plist'
  PLIST_KEYS = frozenset(
      ['LastFullSuccessfulDate', 'LastSuccessfulDate',
       'LastAttemptSystemVersion', 'LastUpdatesAvailable',
       'LastRecommendedUpdatesAvailable', 'RecommendedUpdates'])

  # Yield Events
  # LastFullSuccessfulDate: timestamp when Mac OS X was full udpate.
  # LastSuccessfulDate: tiemstamp when Mac OS X was partially udpate.

  def GetEntries(self, unused_cache=None):
    """Extracts relevant Mac OS X update entries.

    Yields:
      EventObject objects extracted from the plist.
    """
    root = '/'
    key = ''
    version = self.match.get('LastAttemptSystemVersion', u'N/A')
    pending = self.match['LastUpdatesAvailable']

    time = timelib.Timestamp.FromPythonDatetime(
        self.match['LastFullSuccessfulDate'])
    description = u'Last Mac OS X {} full update.'.format(version)
    yield plist_event.PlistEvent(root, key, time, description)

    if pending:
      software = []
      for update in self.match['RecommendedUpdates']:
        software.append(u'{}({})'.format(
            update['Identifier'], update['Product Key']))
      time = timelib.Timestamp.FromPythonDatetime(
          self.match['LastSuccessfulDate'])
      description = u'Last Mac OS {} partially udpate, pending {}: {}.'.format(
          version, pending, u','.join(software))
      yield plist_event.PlistEvent(root, key, time, description)

