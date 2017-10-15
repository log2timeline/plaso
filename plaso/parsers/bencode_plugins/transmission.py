# -*- coding: utf-8 -*-
"""Bencode parser plugin for Transmission BitTorrent files."""

from __future__ import unicode_literals

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import bencode_parser
from plaso.parsers.bencode_plugins import interface


class TransmissionEventData(events.EventData):
  """Transmission BitTorrent event data.

  Attributes:
    destination (str): downloaded file name within .torrent file
    seedtime (int): number of seconds client seeded torrent
  """

  DATA_TYPE = 'p2p:bittorrent:transmission'

  def __init__(self):
    """Initializes event data."""
    super(TransmissionEventData, self).__init__(data_type=self.DATA_TYPE)
    self.destination = None
    self.seedtime = None


class TransmissionPlugin(interface.BencodePlugin):
  """Parse Transmission BitTorrent activity file for current torrents."""

  NAME = 'bencode_transmission'
  DESCRIPTION = 'Parser for Transmission bencoded files.'

  BENCODE_KEYS = frozenset([
      'activity-date', 'done-date', 'added-date', 'destination',
      'seeding-time-seconds'])

  def GetEntries(self, parser_mediator, data=None, **unused_kwargs):
    """Extract data from Transmission's resume folder files.

    This is the main parsing engine for the parser. It determines if
    the selected file is the proper file to parse and extracts current
    running torrents.

    Transmission stores an individual Bencoded file for each active download
    in a folder named resume under the user's application data folder.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      data (Optional[dict[str, object]]): bencode data values.
    """
    seeding_time = data.get('seeding-time-seconds', None)

    event_data = TransmissionEventData()
    event_data.destination = data.get('destination', None)
    # Convert seconds to minutes.
    event_data.seedtime, _ = divmod(seeding_time, 60)

    # Create timeline events based on extracted values.
    timestamp = data.get('added-date', None)
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_ADDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = data.get('done-date', None)
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_FILE_DOWNLOADED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = data.get('activity-date', None)
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_LAST_ACCESS)
      parser_mediator.ProduceEventWithEventData(event, event_data)


bencode_parser.BencodeParser.RegisterPlugin(TransmissionPlugin)
