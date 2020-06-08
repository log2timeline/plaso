# -*- coding: utf-8 -*-
"""Parser for bencoded files."""

from __future__ import unicode_literals

import re
import os

import bencode

from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager


class BencodeParser(interface.FileObjectParser):
  """Parser for bencoded files.

  The Plaso engine calls parsers by their Parse() method. The Parse() function
  deserializes bencoded files using the BitTorrent-bencode library and calls
  plugins (BencodePlugin) registered through the interface by their Process()
  to produce event objects.

  Plugins are how this parser understands the content inside a bencoded file,
  each plugin holds logic specific to a particular bencoded file. See the
  bencode_plugins / directory for examples of how bencode plugins are
  implemented.
  """

  # Regex match for a bencode dictionary followed by a field size.
  _BENCODE_RE = re.compile(b'd[0-9]')

  NAME = 'bencode'
  DESCRIPTION = 'Parser for bencoded files.'

  _plugin_classes = {}

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a bencoded file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    header_data = file_object.read(2)
    if not self._BENCODE_RE.match(header_data):
      raise errors.UnableToParseFile('Not a valid Bencoded file.')

    file_object.seek(0, os.SEEK_SET)
    try:
      decoded_values = bencode.bread(file_object)

    except (IOError, bencode.BencodeDecodeError) as exception:
      diplay_name = parser_mediator.GetDisplayName()
      raise errors.UnableToParseFile(
          '[{0:s}] unable to parse file: {1:s} with error: {2!s}'.format(
              self.NAME, diplay_name, exception))

    if not decoded_values:
      parser_mediator.ProduceExtractionWarning('missing decoded Bencode values')
      return

    bencode_keys = set()
    for key in decoded_values.keys():
      if isinstance(key, bytes):
        # Work-around for issue in bencode 3.0.1 where keys are bytes.
        key = key.decode('utf-8')

      bencode_keys.add(key)

    for plugin in self._plugins:
      if parser_mediator.abort:
        break

      if not bencode_keys.issuperset(plugin.BENCODE_KEYS):
        continue

      logger.debug('Bencode Plugin Used: {0:s}'.format(plugin.NAME))

      try:
        plugin.UpdateChainAndProcess(
            parser_mediator, decoded_values=decoded_values)

      except Exception as exception:  # pylint: disable=broad-except
        parser_mediator.ProduceExtractionWarning((
            'plugin: {0:s} unable to parse Bencode file with error: '
            '{1!s}').format(plugin.NAME, exception))


manager.ParsersManager.RegisterParser(BencodeParser)
