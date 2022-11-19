# -*- coding: utf-8 -*-
"""Bencode parser plugin for Transmission BitTorrent files."""

from plaso.containers import events
from plaso.parsers import bencode_parser
from plaso.parsers.bencode_plugins import interface


class TransmissionEventData(events.EventData):
  """Transmission BitTorrent event data.

  Attributes:
    added_time (dfdatetime.DateTimeValues): date and time the torrent was
        added to Transmission.
    destination (str): path of the downloaded file.
    downloaded_time (dfdatetime.DateTimeValues): date and time the content
        was downloaded.
    last_activity_time (dfdatetime.DateTimeValues): date and time of the last
        download activity.
    seedtime (int): client seed time in number of minutes.
  """

  DATA_TYPE = 'p2p:bittorrent:transmission'

  def __init__(self):
    """Initializes event data."""
    super(TransmissionEventData, self).__init__(data_type=self.DATA_TYPE)
    self.added_time = None
    self.destination = None
    self.downloaded_time = None
    self.last_activity_time = None
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
          and other components, such as storage and dfVFS.
      bencode_file (Optional[BencodeFile]): bencode file.
    """
    # This will raise if unhandled keyword arguments are passed.
    super(TransmissionBencodePlugin, self).Process(parser_mediator, **kwargs)

    root_values = bencode_file.GetValues()

    seeding_time = root_values.GetDecodedValue('seeding-time-seconds')

    event_data = TransmissionEventData()
    event_data.added_time = root_values.GetDateTimeValue('added-date')
    event_data.destination = root_values.GetDecodedValue('destination')
    event_data.downloaded_time = root_values.GetDateTimeValue('done-date')
    event_data.last_activity_time = root_values.GetDateTimeValue(
        'activity-date')
    # Convert seconds to minutes.
    event_data.seedtime, _ = divmod(seeding_time, 60)

    parser_mediator.ProduceEventData(event_data)


bencode_parser.BencodeParser.RegisterPlugin(TransmissionBencodePlugin)
