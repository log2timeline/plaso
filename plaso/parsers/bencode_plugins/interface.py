# -*- coding: utf-8 -*-
"""Bencode parser plugin interface.

BencodePlugin defines the attributes necessary for registration, discovery and
operation of plugins for bencoded files which will be used by BencodeParser.
"""

from __future__ import unicode_literals

import abc

from plaso.parsers import plugins


class BencodePlugin(plugins.BasePlugin):
  """Bencode parser plugin interface."""

  # BENCODE_KEYS is a list of keys required by a plugin.
  # This is expected to be overridden by the processing plugin.
  # Ex. frozenset(['activity-date', 'done-date'])
  BENCODE_KEYS = frozenset(['any'])

  # This is expected to be overridden by the processing plugin.
  # URLS should contain a list of URLs with additional information about
  # this key or value.
  # Ex. ['https://wiki.theory.org/BitTorrentSpecification#Bencoding']
  URLS = []

  NAME = 'bencode_plugin'

  def _GetDecodedValue(self, decoded_values, name):
    """Retrieves a decoded value.

    Args:
      decoded_values (collections.OrderedDict[bytes|str, object]): decoded
          values.
      name (str): name of the value.

    Returns:
      object: decoded value or None if not available.
    """
    value = decoded_values.get(name, None)
    if value is None:
      # Work-around for issue in bencode 3.0.1 where keys are bytes.
      name_as_byte_stream = name.encode('utf-8')
      value = decoded_values.get(name_as_byte_stream, None)

    if isinstance(value, bytes):
      # Work-around for issue in bencode 3.0.1 where string valuse are bytes.
      value = value.decode('utf-8')

    return value

  # pylint: disable=arguments-differ
  @abc.abstractmethod
  def Process(self, parser_mediator, decoded_values=None, **kwargs):
    """Extracts events from the values of entries within a bencoded file.

    This is the main method that a Bencode plugin needs to implement.

    The contents of the bencode keys defined in BENCODE_KEYS can be made
    available to the plugin as both a matched{'KEY': 'value'} and as the
    entire bencoded data dictionary. The plugin should implement logic to parse
    the most relevant data set into a useful event for incorporation into the
    Plaso timeline.

    The attributes for a BencodeEvent should include the following:
      root = Root key this event was extracted from.
      key = Key the value resided in.
      time = Date this artifact was created in micro seconds (usec) from
             January 1, 1970 00:00:00 UTC.
      desc = Short description.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      decoded_values (Optional[collections.OrderedDict[bytes|str, object]]):
          decoded values.
    """
