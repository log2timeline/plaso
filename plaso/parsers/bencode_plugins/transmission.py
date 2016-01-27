# -*- coding: utf-8 -*-
"""Bencode parser plugin for Transmission BitTorrent files."""

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.parsers import bencode_parser
from plaso.parsers.bencode_plugins import interface


class TransmissionEvent(time_events.PosixTimeEvent):
  """Convenience class for a Transmission BitTorrent activity event."""

  DATA_TYPE = u'p2p:bittorrent:transmission'

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
    # Convert seconds to minutes.
    self.seedtime, _ = divmod(seedtime, 60)


class TransmissionPlugin(interface.BencodePlugin):
  """Parse Transmission BitTorrent activity file for current torrents."""

  NAME = u'bencode_transmission'
  DESCRIPTION = u'Parser for Transmission bencoded files.'

  BENCODE_KEYS = frozenset([
      u'activity-date', u'done-date', u'added-date', u'destination',
      u'seeding-time-seconds'])

  def GetEntries(self, parser_mediator, data=None, **unused_kwargs):
    """Extract data from Transmission's resume folder files.

    This is the main parsing engine for the parser. It determines if
    the selected file is the proper file to parse and extracts current
    running torrents.

    Transmission stores an individual Bencoded file for each active download
    in a folder named resume under the user's application data folder.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      data: Optional bencode data in dictionary form.
    """
    # Place the obtained values into the event.
    destination = data.get(u'destination', None)
    seeding_time = data.get(u'seeding-time-seconds', None)

    # Create timeline events based on extracted values.
    if data.get(u'added-date', 0):
      event_object = TransmissionEvent(
          data.get(u'added-date'), eventdata.EventTimestamp.ADDED_TIME,
          destination, seeding_time)
      parser_mediator.ProduceEvent(event_object)

    if data.get(u'done-date', 0):
      event_object = TransmissionEvent(
          data.get(u'done-date'), eventdata.EventTimestamp.FILE_DOWNLOADED,
          destination, seeding_time)
      parser_mediator.ProduceEvent(event_object)

    if data.get(u'activity-date', None):
      event_object = TransmissionEvent(
          data.get(u'activity-date'), eventdata.EventTimestamp.ACCESS_TIME,
          destination, seeding_time)
      parser_mediator.ProduceEvent(event_object)


bencode_parser.BencodeParser.RegisterPlugin(TransmissionPlugin)
