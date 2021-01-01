# -*- coding: utf-8 -*-
"""Bencode parser plugin interface.

BencodePlugin defines the attributes necessary for registration, discovery and
operation of plugins for bencoded files which will be used by BencodeParser.
"""

import abc

from plaso.parsers import plugins


class BencodePlugin(plugins.BasePlugin):
  """Bencode parser plugin interface."""

  NAME = 'bencode_plugin'
  DATA_FORMAT = 'Bencoded file'

  # This is expected to be overridden by the processing plugin.
  # URLS should contain a list of URLs with additional information about
  # this key or value.
  # Ex. ['https://wiki.theory.org/BitTorrentSpecification#Bencoding']
  URLS = []

  # _BENCODE_KEYS is a list of keys required by a plugin.
  # This is expected to be overridden by the processing plugin.
  # Ex. frozenset(['activity-date', 'done-date'])
  _BENCODE_KEYS = frozenset(['any'])

  def CheckRequiredKeys(self, bencode_file):
    """Check if the bencode file has the minimal keys required by the plugin.

    Args:
      bencode_file (BencodeFile): bencode file.

    Returns:
      bool: True if the bencode file has the minimum keys defined by the plugin,
          or False if it does not or no required keys are defined. The bencode
          file can have more keys than specified by the plugin and still return
          True.
    """
    if not self._BENCODE_KEYS:
      return False

    return bencode_file.keys.issuperset(self._BENCODE_KEYS)

  # pylint: disable=arguments-differ
  @abc.abstractmethod
  def Process(self, parser_mediator, bencode_file=None, **kwargs):
    """Extracts events from the values of entries within a bencode file.

    This is the main method that a Bencode plugin needs to implement.

    The contents of the bencode keys defined in _BENCODE_KEYS can be made
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
      bencode_file (Optional[BencodeFile]): bencode file.
    """
