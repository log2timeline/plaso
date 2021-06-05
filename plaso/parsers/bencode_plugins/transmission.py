# -*- coding: utf-8 -*-
"""Bencode parser plugin for Transmission BitTorrent files."""

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import bencode_parser
from plaso.parsers.bencode_plugins import interface


class TransmissionEventData(events.EventData):
  """Transmission BitTorrent event data.

  Attributes:
    destination (str): path of the downloaded file.
    seedtime (int): client seed time in number of minutes.
  """

  DATA_TYPE = 'p2p:bittorrent:transmission'

  def __init__(self):
    """Initializes event data."""
    super(TransmissionEventData, self).__init__(data_type=self.DATA_TYPE)
    self.destination = None
    self.seedtime = None


class TransmissionBencodePlugin(interface.BencodePlugin):
  """Parse Transmission BitTorrent activity file for current torrents.

  Transmission stores an individual Bencoded file for each active download
  in a folder named resume under the user's application data folder.
  """

  NAME = 'bencode_transmission'
  DATA_FORMAT = 'Transmission BitTorrent activity file'

  _BENCODE_KEYS = frozenset([
      'activity-date', 'added-date', 'destination', 'done-date',
      'seeding-time-seconds'])

  def Process(self, parser_mediator, bencode_file=None, **kwargs):
    """Extracts events from a Transmission's resume folder file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      bencode_file (Optional[BencodeFile]): bencode file.
    """
    # This will raise if unhandled keyword arguments are passed.
    super(TransmissionBencodePlugin, self).Process(parser_mediator, **kwargs)

    destination = bencode_file.GetDecodedValue('destination')
    seeding_time = bencode_file.GetDecodedValue('seeding-time-seconds')

    event_data = TransmissionEventData()
    event_data.destination = destination
    # Convert seconds to minutes.
    event_data.seedtime, _ = divmod(seeding_time, 60)

    timestamp = bencode_file.GetDecodedValue('added-date')
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_ADDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = bencode_file.GetDecodedValue('done-date')
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_FILE_DOWNLOADED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = bencode_file.GetDecodedValue('activity-date')
    if timestamp:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_LAST_ACCESS)
      parser_mediator.ProduceEventWithEventData(event, event_data)


bencode_parser.BencodeParser.RegisterPlugin(TransmissionBencodePlugin)
