# -*- coding: utf-8 -*-
"""The bencode parser event formatters."""

from plaso.formatters import interface
from plaso.formatters import manager


class TransmissionEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Transmission active torrents event."""

  DATA_TYPE = 'p2p:bittorrent:transmission'

  SOURCE_LONG = 'Transmission Active Torrents'
  SOURCE_SHORT = 'TORRENT'

  FORMAT_STRING_SEPARATOR = u'; '

  FORMAT_STRING_PIECES = [
      u'Saved to {destination}',
      u'Minutes seeded: {seedtime}']


class UTorrentEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a BitTorrent uTorrent active torrents event."""

  DATA_TYPE = 'p2p:bittorrent:utorrent'

  SOURCE_LONG = 'uTorrent Active Torrents'
  SOURCE_SHORT = 'TORRENT'

  FORMAT_STRING_SEPARATOR = u'; '

  FORMAT_STRING_PIECES = [
      u'Torrent {caption}',
      u'Saved to {path}',
      u'Minutes seeded: {seedtime}']


manager.FormattersManager.RegisterFormatters([
    TransmissionEventFormatter, UTorrentEventFormatter])
