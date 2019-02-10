# -*- coding: utf-8 -*-
"""Bencode parser plugin for uTorrent files."""

from __future__ import unicode_literals

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import bencode_parser
from plaso.parsers.bencode_plugins import interface


class UTorrentEventData(events.EventData):
  """uTorrent event data.

  Attributes:
    caption (str): official name of package
    path (str): Torrent download location
    seedtime (int): number of seconds client seeded torrent
  """

  DATA_TYPE = 'p2p:bittorrent:utorrent'

  def __init__(self):
    """Initializes event data."""
    super(UTorrentEventData, self).__init__(data_type=self.DATA_TYPE)
    self.caption = None
    self.path = None
    self.seedtime = None


class UTorrentPlugin(interface.BencodePlugin):
  """Plugin to extract uTorrent active torrent events."""

  NAME = 'bencode_utorrent'
  DESCRIPTION = 'Parser for uTorrent bencoded files.'

  # The following set is used to determine if the bencoded data is appropriate
  # for this plugin. If there's a match, the entire bencoded data block is
  # returned for analysis.
  BENCODE_KEYS = frozenset(['.fileguard'])

  def GetEntries(self, parser_mediator, data=None, **unused_kwargs):
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

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      data (Optional[dict[str, object]]): bencode data values.
    """
    # Walk through one of the torrent keys to ensure it's from a valid file.
    for key, value in iter(data.items()):
      if not '.torrent' in key:
        continue

      caption = value.get('caption')
      path = value.get('path')
      seedtime = value.get('seedtime')
      if not caption or not path or seedtime < 0:
        raise errors.WrongBencodePlugin(self.NAME)

    for torrent, value in iter(data.items()):
      if not '.torrent' in torrent:
        continue

      event_data = UTorrentEventData()
      event_data.caption = value.get('caption', None)
      event_data.path = value.get('path', None)

      # Convert seconds to minutes.
      seedtime = value.get('seedtime', None)
      event_data.seedtime, _ = divmod(seedtime, 60)

      # Create timeline events based on extracted values.
      for event_key, event_value in iter(value.items()):
        if event_key == 'added_on':
          date_time = dfdatetime_posix_time.PosixTime(timestamp=event_value)
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_ADDED)
          parser_mediator.ProduceEventWithEventData(event, event_data)

        elif event_key == 'completed_on':
          date_time = dfdatetime_posix_time.PosixTime(timestamp=event_value)
          event = time_events.DateTimeValuesEvent(
              date_time, definitions.TIME_DESCRIPTION_FILE_DOWNLOADED)
          parser_mediator.ProduceEventWithEventData(event, event_data)

        elif event_key == 'modtimes':
          for modtime in event_value:
            # Some values are stored as 0, skip those.
            if not modtime:
              continue

            date_time = dfdatetime_posix_time.PosixTime(timestamp=modtime)
            event = time_events.DateTimeValuesEvent(
                date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
            parser_mediator.ProduceEventWithEventData(event, event_data)


bencode_parser.BencodeParser.RegisterPlugin(UTorrentPlugin)
