# -*- coding: utf-8 -*-
"""Bencode parser plugin for uTorrent active torrent files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.parsers import bencode_parser
from plaso.parsers.bencode_plugins import interface


class UTorrentEventData(events.EventData):
  """uTorrent active torrent event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date and time the torrent was
        added to Transmission.
    caption (str): official name of package.
    destination (str): path of the downloaded file.
    downloaded_time (dfdatetime.DateTimeValues): date and time the content
        was downloaded.
    modification_times (list[dfdatetime.DateTimeValues]): modification dates
        and times.
    seedtime (int): client seed time in number of minutes.
  """

  DATA_TYPE = 'p2p:bittorrent:utorrent'

  def __init__(self):
    """Initializes event data."""
    super(UTorrentEventData, self).__init__(data_type=self.DATA_TYPE)
    self.added_time = None
    self.caption = None
    self.destination = None
    self.downloaded_time = None
    self.modification_times = None
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
          and other components, such as storage and dfVFS.
      bencode_file (Optional[BencodeFile]): bencode file.
    """
    # This will raise if unhandled keyword arguments are passed.
    super(UTorrentBencodePlugin, self).Process(parser_mediator, **kwargs)

    root_values = bencode_file.GetValues()

    for key, value in root_values.GetValues():
      if not '.torrent' in key:
        continue

      torrent_values = bencode_parser.BencodeValues(value)

      seedtime = torrent_values.GetDecodedValue('seedtime')

      modification_times = []
      for timestamp in torrent_values.GetDecodedValue('modtimes') or []:
        # Ignore modification timestamps stored as 0.
        if timestamp:
          date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
          modification_times.append(date_time)

      event_data = UTorrentEventData()
      event_data.added_time = torrent_values.GetDateTimeValue('added_on')
      event_data.caption = torrent_values.GetDecodedValue('caption')
      event_data.destination = torrent_values.GetDecodedValue('path')
      event_data.downloaded_time = torrent_values.GetDateTimeValue(
          'completed_on')
      event_data.modification_times = modification_times or None
      # Convert seconds to minutes.
      event_data.seedtime, _ = divmod(seedtime, 60)

    parser_mediator.ProduceEventData(event_data)


bencode_parser.BencodeParser.RegisterPlugin(UTorrentBencodePlugin)
