# -*- coding: utf-8 -*-
"""Bencode parser plugin for uTorrent active torrent files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import bencode_parser
from plaso.parsers.bencode_plugins import interface


class UTorrentEventData(events.EventData):
  """uTorrent active torrent event data.

  Attributes:
    caption (str): official name of package.
    destination (str): path of the downloaded file.
    seedtime (int): client seed time in number of minutes.
  """

  DATA_TYPE = 'p2p:bittorrent:utorrent'

  def __init__(self):
    """Initializes event data."""
    super(UTorrentEventData, self).__init__(data_type=self.DATA_TYPE)
    self.caption = None
    self.path = None
    self.seedtime = None


class UTorrentBencodePlugin(interface.BencodePlugin):
  """Plugin to extract parse uTorrent active torrent files.

  uTorrent creates a file, resume.dat, and a backup, resume.dat.old, to
  for all active torrents. This is typically stored in the user's
  application data folder.

  These files, at a minimum, contain a '.fileguard' key and a dictionary
  with a key name for a particular download with a '.torrent' file
  extension.
  """

  NAME = 'bencode_utorrent'
  DATA_FORMAT = 'uTorrent active torrent file'

  # The following set is used to determine if the bencoded data is appropriate
  # for this plugin. If there's a match, the entire bencoded data block is
  # returned for analysis.
  _BENCODE_KEYS = frozenset(['.fileguard'])

  def Process(self, parser_mediator, bencode_file=None, **kwargs):
    """Extracts events from an uTorrent active torrent file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      bencode_file (Optional[BencodeFile]): bencode file.
    """
    # This will raise if unhandled keyword arguments are passed.
    super(UTorrentBencodePlugin, self).Process(parser_mediator, **kwargs)

    for key, value in bencode_file.GetDecodedValues():
      if not '.torrent' in key:
        continue

      bencoded_values = bencode_parser.BencodeValues(value)
      caption = bencoded_values.GetDecodedValue('caption')
      path = bencoded_values.GetDecodedValue('path')
      seedtime = bencoded_values.GetDecodedValue('seedtime')
      if not caption or not path or seedtime < 0:
        parser_mediator.ProduceExtractionWarning(
            'key: {0:s} is missing valid caption, path and seedtime'.format(
                key))
        continue

      event_data = UTorrentEventData()
      event_data.caption = caption
      event_data.path = path
      # Convert seconds to minutes.
      event_data.seedtime, _ = divmod(seedtime, 60)

      # Create timeline events based on extracted values.
      for event_key, event_value in value.items():
        if isinstance(event_key, bytes):
          # Work-around for issue in bencode 3.0.1 where keys are bytes.
          event_key = event_key.decode('utf-8')

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


bencode_parser.BencodeParser.RegisterPlugin(UTorrentBencodePlugin)
