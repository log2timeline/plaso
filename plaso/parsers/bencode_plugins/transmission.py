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
"""This file contains a bencode plugin for Transmission BitTorrent data."""

from plaso.lib import event
from plaso.lib import eventdata
from plaso.parsers.bencode_plugins import interface


class TransmissionEvent(event.PosixTimeEvent):
  """Convenience class for a Transmission BitTorrent activity event."""

  DATA_TYPE = 'p2p:bittorrent:transmission'

  def __init__(self, timestamp, timestamp_description, destination, seedtime):
    """Initializes the event.

    Args:
      timestamp: The POSIX timestamp of the event.
      timestamp_desc: A short description of the meaning of the timestamp.
      destination: Downloaded file name within .torrent file
      seedtime: Number of seconds client seeded torrent
    """
    super(TransmissionEvent, self).__init__(timestamp, timestamp_description)
    self.destination = destination
    self.seedtime = seedtime // 60  # Convert seconds to minutes.


class TransmissionPlugin(interface.BencodePlugin):
  """Parse Transmission BitTorrent activity file for current torrents."""

  NAME = 'bencode_transmission'

  BENCODE_KEYS = frozenset(
      ['activity-date', 'done-date', 'added-date', 'destination',
       'seeding-time-seconds'])

  def GetEntries(self, data, **unused_kwargs):
    """Extract data from Transmission's resume folder files.

    This is the main parsing engine for the parser. It determines if
    the selected file is the proper file to parse and extracts current
    running torrents.

    Transmission stores an individual Bencoded file for each active download
    in a folder named resume under the user's application data folder.

    Args:
      data: Bencode data in dictionary form.

    Yields:
      An EventObject (TransmissionEvent) that contains the extracted
      attributes.
    """

    # Place the obtained values into the event.
    destination = data.get('destination', None)
    seeding_time = data.get('seeding-time-seconds', None)

    # Create timeline events based on extracted values.
    if data.get('added-date', 0):
      yield TransmissionEvent(
          data.get('added-date'), eventdata.EventTimestamp.ADDED_TIME,
          destination, seeding_time)

    if data.get('done-date', 0):
      yield TransmissionEvent(
          data.get('done-date'), eventdata.EventTimestamp.FILE_DOWNLOADED,
          destination, seeding_time)

    if data.get('activity-date', None):
      yield TransmissionEvent(
          data.get('activity-date'), eventdata.EventTimestamp.ACCESS_TIME,
          destination, seeding_time)
