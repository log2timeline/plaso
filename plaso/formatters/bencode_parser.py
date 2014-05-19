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
"""Formatter for bencode parser events."""

from plaso.lib import eventdata


class uTorrentFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for a BitTorrent uTorrent active torrents."""

  DATA_TYPE = 'p2p:bittorrent:utorrent'

  SOURCE_LONG = 'uTorrent Active Torrents'
  SOURCE_SHORT = 'TORRENT'

  FORMAT_STRING_SEPARATOR = u'; '

  FORMAT_STRING_PIECES = [u'Torrent {caption}',
                          u'Saved to {path}',
                          u'Minutes seeded: {seedtime}']


class TransmissionFormatter(eventdata.ConditionalEventFormatter):
  """Formatter for a Transmission active torrents."""

  DATA_TYPE = 'p2p:bittorrent:transmission'

  SOURCE_LONG = 'Transmission Active Torrents'
  SOURCE_SHORT = 'TORRENT'

  FORMAT_STRING_SEPARATOR = u'; '

  FORMAT_STRING_PIECES = [u'Saved to {destination}',
                          u'Minutes seeded: {seedtime}']
