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
"""This file contains a bencode plugin for uTorrent data."""

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.parsers.bencode_plugins import interface


class UTorrentEventContainer(event.EventContainer):
  """Convenience class for a uTorrent active torrents history entries."""
  DATA_TYPE = 'p2p:bittorrent:utorrent'

  def __init__(self, path, caption, seedtime):
    """Initialize the event container.

    Args:
      path: Torrent download location
      caption: Official name of package
      seedtime: Number of seconds client seeded torrent
    """
    super(UTorrentEventContainer, self).__init__()
    self.path = path
    self.caption = caption
    self.seedtime = seedtime // 60 # Convert seconds to minutes.


class UTorrentPlugin(interface.BencodePlugin):
  """Plugin to extract uTorrent active torrent events."""

  NAME = 'bencode_utorrent'

  # The following set is used to determine if the bencoded data is appropriate
  # for this plugin. If there's a match, the entire bencoded data block is
  # returned for analysis.
  BENCODE_KEYS = frozenset(['.fileguard'])

  def GetEntries(self, unused_cache=None):
    """Extracts uTorrent active torrents.

    This is the main parsing engine for the plugin. It determines if
    the selected file is the proper file to parse and extracts current
    running torrents.

    interface.Process() checks for the given BENCODE_KEYS set, ensures
    that it matches, and then passes the bencoded data to this function for
    parsing. This plugin then parses the entire set of bencoded data to extract
    the variable file-name keys to retrieve their values.

    uTorrent creates a file, resume.dat, and a backup, resume.dat.old, to
    for all active torrents. This is typically stored in the user's
    application data folder.

    These files, at a minimum, contain a '.fileguard' key and a dictionary
    with a key name for a particular download with a '.torrent' file
    extension.

    Yields:
      An EventContainer (UTorrentEventContainer) with extracted
      EventObjects that contain the extracted attributes.
    """

    # Walk through one of the torrent keys to ensure it's from a valid file.
    for key, value in self.data.iteritems():
      if not u'.torrent' in key:
        continue

      caption = value.get('caption')
      path = value.get('path')
      seedtime = value.get('seedtime')
      if not caption or not path or seedtime < 0:
        raise errors.WrongBencodePlugin(self.plugin_name)

    for torrent, value in self.data.iteritems():
      if not u'.torrent' in torrent:
        continue

      # Place the obtained values into the event container.
      container = UTorrentEventContainer(
          value.get('path'),
          value.get('caption'),
          value.get('seedtime'))

      # Create timeline events based on extracted values.
      for eventkey, eventvalue in value.iteritems():
        if eventkey == 'added_on':
          container.Append(event.PosixTimeEvent(
              eventvalue,
              eventdata.EventTimestamp.ADDED_TIME,
              container.DATA_TYPE))
        elif eventkey == 'completed_on':
          container.Append(event.PosixTimeEvent(
              eventvalue,
              eventdata.EventTimestamp.FILE_DOWNLOADED,
              container.DATA_TYPE))
        elif eventkey == 'modtimes':
          for modtime in eventvalue:
            # Some values are stored as 0, skip those.
            if not modtime:
              continue
            container.Append(event.PosixTimeEvent(
                modtime,
                eventdata.EventTimestamp.MODIFICATION_TIME,
                container.DATA_TYPE))

      yield container
