# -*- coding: utf-8 -*-
"""Parser for binary and text Property List (plist) files."""

from __future__ import unicode_literals

import biplist

from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager


class PlistParser(interface.FileObjectParser):
  """Parser for binary and text Property List (plist) files.

  The Plaso engine calls parsers by their Parse() method. This parser's
  Parse() has GetTopLevel() which deserializes plist files using the biplist
  library and calls plugins (PlistPlugin) registered through the
  interface by their Process() to produce event objects.

  Plugins are how this parser understands the content inside a plist file,
  each plugin holds logic specific to a particular plist file. See the
  interface and plist_plugins/ directory for examples of how plist plugins are
  implemented.
  """

  NAME = 'plist'
  DESCRIPTION = 'Parser for binary and text plist files.'

  _plugin_classes = {}

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: a format specification or None if not available.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'bplist', offset=0)
    return format_specification

  def GetTopLevel(self, file_object):
    """Returns the deserialized content of a plist as a dictionary object.

    Args:
      file_object (dfvfs.FileIO): a file-like object to parse.

    Returns:
      dict[str, object]: contents of the plist.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    try:
      top_level_object = biplist.readPlist(file_object)

    except (biplist.InvalidPlistException,
            biplist.NotBinaryPlistException) as exception:
      raise errors.UnableToParseFile(
          'Unable to parse plist with error: {0!s}'.format(exception))

    return top_level_object

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a plist file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    filename = parser_mediator.GetFilename()
    file_size = file_object.get_size()

    if file_size <= 0:
      raise errors.UnableToParseFile(
          'File size: {0:d} bytes is less equal 0.'.format(file_size))

    # 50MB is 10x larger than any plist seen to date.
    if file_size > 50000000:
      raise errors.UnableToParseFile(
          'File size: {0:d} bytes is larger than 50 MB.'.format(file_size))

    top_level_object = self.GetTopLevel(file_object)
    if not top_level_object:
      raise errors.UnableToParseFile(
          'Unable to parse: {0:s} skipping.'.format(filename))

    filename_lower_case = filename.lower()
    top_level_keys = set(top_level_object.keys())

    found_matching_plugin = False
    for plugin in self._plugins:
      if parser_mediator.abort:
        break

      if not plugin.PLIST_PATH_FILTERS:
        path_filter_match = True
      else:
        path_filter_match = False
        for path_filter in plugin.PLIST_PATH_FILTERS:
          if path_filter.Match(filename_lower_case):
            path_filter_match = True

      if (not path_filter_match or
          not top_level_keys.issuperset(plugin.PLIST_KEYS)):
        continue

      logger.debug('Plist plugin used: {0:s}'.format(plugin.NAME))

      try:
        plugin.UpdateChainAndProcess(
            parser_mediator, top_level=top_level_object)
        found_matching_plugin = True

      except Exception as exception:  # pylint: disable=broad-except
        parser_mediator.ProduceExtractionWarning((
            'plugin: {0:s} unable to parse plist file with error: '
            '{1!s}').format(plugin.NAME, exception))

    if not found_matching_plugin and self._default_plugin:
      self._default_plugin.UpdateChainAndProcess(
          parser_mediator, top_level=top_level_object)


manager.ParsersManager.RegisterParser(PlistParser)
