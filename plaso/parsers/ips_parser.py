# -*- coding: utf-8 -*-
"""Parser for IPS formatted log files."""

import json

from dfvfs.helpers import text_file

from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class IPSFile(object):
  """IPS log file.

  Attributes:
    content (dict[str, object]): JSON serialized IPS log file content.
    header (dict[str, object]): JSON serialized IPS log file header.
  """

  def __init__(self):
    """Initializes an IPS log file."""
    super(IPSFile, self).__init__()
    self.content = None
    self.header = None

  def Open(self, text_file_object):
    """Opens an IPS log file.

    Args:
      text_file_object (text_file.TextFile): text file object.
    Raises:
      ValueError: if the file object is missing.
    """
    if not text_file_object:
      raise ValueError('Missing text file object.')

    self.header = json.loads(text_file_object.readline())
    self.content = json.loads('\n'.join(text_file_object.readlines()))


class IPSParser(interface.FileEntryParser):
  """Parses IPS formatted log files."""

  NAME = 'ips'
  DATA_FORMAT = 'IPS log file'

  _plugin_classes = {}

  def ParseFileEntry(self, parser_mediator, file_entry):
    """Parses an IPS formatted log file entry.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_entry (dfvfs.FileEntry): file entry to be parsed.
    """
    file_object = file_entry.GetFileObject()
    text_file_object = text_file.TextFile(file_object)

    try:
      ips_file_object = IPSFile()
      ips_file_object.Open(text_file_object)

    except ValueError:
      raise errors.WrongParser('Invalid IPS file.')

    for plugin_name, plugin in self._plugins_per_name.items():
      if parser_mediator.abort:
        break

      profiling_name = '/'.join([self.NAME, plugin.NAME])

      parser_mediator.SampleFormatCheckStartTiming(profiling_name)

      try:
        result = plugin.CheckRequiredKeys(ips_file_object)
      finally:
        parser_mediator.SampleFormatCheckStopTiming(profiling_name)

      if not result:
        continue

      parser_mediator.SampleStartTiming(profiling_name)

      try:
        plugin.UpdateChainAndProcess(
            parser_mediator, ips_file=ips_file_object)

      except Exception as exception:  # pylint: disable=broad-except
        parser_mediator.ProduceExtractionWarning((
            'plugin: {0:s} unable to parse IPS file with error: {1!s}').format(
                plugin_name, exception))

      finally:
        parser_mediator.SampleStopTiming(profiling_name)


manager.ParsersManager.RegisterParser(IPSParser)
