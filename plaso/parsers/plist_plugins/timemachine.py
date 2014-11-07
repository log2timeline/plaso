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
"""This file contains a TimeMachine plist plugin in Plaso."""

import construct

from plaso.events import plist_event
from plaso.parsers import plist
from plaso.parsers.plist_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class TimeMachinePlugin(interface.PlistPlugin):
  """Basic plugin to extract time machine hardisk and the backups."""

  NAME = 'plist_timemachine'
  DESCRIPTION = u'Parser for TimeMachine plist files.'

  PLIST_PATH = 'com.apple.TimeMachine.plist'
  PLIST_KEYS = frozenset(['Destinations', 'RootVolumeUUID'])

  # Generated events:
  # DestinationID: remote UUID hard disk where the backup is done.
  # BackupAlias: structure that contains the extra information from the
  #              destinationID.
  # SnapshotDates: list of the backup dates.

  TM_BACKUP_ALIAS = construct.Struct(
      'tm_backup_alias',
      construct.Padding(10),
      construct.PascalString('value', length_field=construct.UBInt8('length')))

  def GetEntries(self, parser_context, match=None, **unused_kwargs):
    """Extracts relevant TimeMachine entries.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      match: Optional dictionary containing keys extracted from PLIST_KEYS.
             The default is None.
    """
    root = '/Destinations'
    key = 'item/SnapshotDates'

    # For each TimeMachine devices.
    for destination in match['Destinations']:
      hd_uuid = destination['DestinationID']
      if not hd_uuid:
        hd_uuid = u'Unknown device'
      alias = destination['BackupAlias']
      try:
        alias = self.TM_BACKUP_ALIAS.parse(alias).value
      except construct.FieldError:
        alias = u'Unknown alias'
      # For each Backup.
      for timestamp in destination['SnapshotDates']:
        description = u'TimeMachine Backup in {0:s} ({1:s})'.format(
            alias, hd_uuid)
        event_object = plist_event.PlistEvent(root, key, timestamp, description)
        parser_context.ProduceEvent(event_object, plugin_name=self.NAME)


plist.PlistParser.RegisterPlugin(TimeMachinePlugin)
