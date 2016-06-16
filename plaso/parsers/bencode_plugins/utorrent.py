# -*- coding: utf-8 -*-
"""Bencode parser plugin for uTorrent files."""

from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import bencode_parser
from plaso.parsers.bencode_plugins import interface


class UTorrentEvent(time_events.PosixTimeEvent):
  """Convenience class for a uTorrent active torrents history entries."""

  DATA_TYPE = u'p2p:bittorrent:utorrent'

  def __init__(
      self, timestamp, timestamp_description, path, caption, seedtime):
    """Initialize the event.

    Args:
      path: Torrent download location
      caption: Official name of package
      seedtime: Number of seconds client seeded torrent
    """
    super(UTorrentEvent, self).__init__(timestamp, timestamp_description)
    self.path = path
    self.caption = caption
    # Convert seconds to minutes.
    self.seedtime, _ = divmod(seedtime, 60)


class UTorrentPlugin(interface.BencodePlugin):
  """Plugin to extract uTorrent active torrent events."""

  NAME = u'bencode_utorrent'
  DESCRIPTION = u'Parser for uTorrent bencoded files.'

  # The following set is used to determine if the bencoded data is appropriate
  # for this plugin. If there's a match, the entire bencoded data block is
  # returned for analysis.
  BENCODE_KEYS = frozenset([u'.fileguard'])

  def GetEntries(
      self, parser_mediator, data=None, **unused_kwargs):
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
      parser_mediator: A parser mediator object (instance of ParserMediator).
      data: Optional bencode data in dictionary form.
    """
    # Walk through one of the torrent keys to ensure it's from a valid file.
    for key, value in iter(data.items()):
      if not u'.torrent' in key:
        continue

      caption = value.get(u'caption')
      path = value.get(u'path')
      seedtime = value.get(u'seedtime')
      if not caption or not path or seedtime < 0:
        raise errors.WrongBencodePlugin(self.NAME)

    for torrent, value in iter(data.items()):
      if not u'.torrent' in torrent:
        continue

      path = value.get(u'path', None)
      caption = value.get(u'caption', None)
      seedtime = value.get(u'seedtime', None)

      # Create timeline events based on extracted values.
      for event_key, event_value in iter(value.items()):
        if event_key == u'added_on':
          event_object = UTorrentEvent(
              event_value, eventdata.EventTimestamp.ADDED_TIME,
              path, caption, seedtime)
          parser_mediator.ProduceEvent(event_object)

        elif event_key == u'completed_on':
          event_object = UTorrentEvent(
              event_value, eventdata.EventTimestamp.FILE_DOWNLOADED,
              path, caption, seedtime)
          parser_mediator.ProduceEvent(event_object)

        elif event_key == u'modtimes':
          for modtime in event_value:
            # Some values are stored as 0, skip those.
            if not modtime:
              continue

            event_object = UTorrentEvent(
                modtime, eventdata.EventTimestamp.MODIFICATION_TIME,
                path, caption, seedtime)
            parser_mediator.ProduceEvent(event_object)


bencode_parser.BencodeParser.RegisterPlugin(UTorrentPlugin)
