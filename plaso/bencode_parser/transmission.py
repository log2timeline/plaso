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
"""This file contains a bencode plugin for Transmission BitTorrent data."""

from plaso.lib import bencode_interface
from plaso.lib import event
from plaso.lib import eventdata


class TransmissionEventContainer(event.EventContainer):
  """Convenience class for a Transmission BitTorrent activity container."""
  DATA_TYPE = 'p2p:bittorrent:transmission'

  def __init__(self, destination, seedtime):
    """Initializes the event container.

    Args:
      destination: Downloaded file name within .torrent file
      seedtime: Number of seconds client seeded torrent
    """
    super(TransmissionEventContainer, self).__init__()
    self.destination = destination
    self.seedtime = seedtime // 60  # Convert seconds to minutes.


class TransmissionPlugin(bencode_interface.BencodePlugin):
  """Parse Transmission BitTorrent activity file for current torrents."""

  BENCODE_KEYS = frozenset(['activity-date', 'done-date', 'added-date',
                            'destination', 'seeding-time-seconds'])

  def GetEntries(self):
    """Extract data from Transmission's resume folder files.

    This is the main parsing engine for the parser. It determines if
    the selected file is the proper file to parse and extracts current
    running torrents.

    Transmission stores an individual Bencoded file for each active download
    in a folder named resume under the user's application data folder.

    Returns:
      An EventContainer (TransmissionEventContainer) with extracted
      EventObjects that contain the extracted attributes.
    """

    # Place the obtained values into the event container.
    container = TransmissionEventContainer(
        self.data['destination'],
        self.data['seeding-time-seconds'])

    # Create timeline events based on extracted values.
    container.Append(event.PosixTimeEvent(
        self.data['added-date'],
        eventdata.EventTimestamp.ADDED_TIME,
        container.DATA_TYPE))

    container.Append(event.PosixTimeEvent(
        self.data['done-date'],
        eventdata.EventTimestamp.FILE_DOWNLOADED,
        container.DATA_TYPE))

    container.Append(event.PosixTimeEvent(
        self.data['activity-date'],
        eventdata.EventTimestamp.ACCESS_TIME,
        container.DATA_TYPE))

    yield container
