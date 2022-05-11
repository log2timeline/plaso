# -*- coding: utf-8 -*-
"""Parser for ips formatted log files. Each file is a single event."""

import json
import re
import yaml

from yaml.scanner import ScannerError

from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager


class IpsFile(object):
  """ips log file"""

  def __init__(self):
    """Initializes an ips log """
    super(IpsFile, self).__init__()
    self.header = None
    self.content = None

  def GetContent(self, raw_content):
    """Extracts the header from the raw content into a json structure.

      Agrs:
        raw_content (str): content of the ips log as a string
    """
    if not isinstance(raw_content, str):
      return None

    content = re.search('}\n({.+)', raw_content, re.DOTALL)
    if content:
      try:
        structured_content = yaml.safe_load(content.group(1))
        return structured_content

      except (ScannerError, AttributeError):
        return None

    return None

  def GetHeader(self, raw_content):
    """Extracts the header from the raw content into a json structure.

      Agrs:
        raw_content (str): content of the ips log as a string
    """
    if not isinstance(raw_content, str):
      return None

    header = re.search('{.+?}', raw_content)

    if header:
      try:
        structured_header = json.loads(header.group())
        return structured_header

      except (json.decoder.JSONDecodeError, TypeError):
        return None

    return None

  def Open(self, file_object):
    """Opens an ips log file.

      Args:
      file_object (dfvfs.FileIO): file-like object.

      Raises:
        ValueError: if the file object is missing.
    """

    if not file_object:
      raise ValueError('Missing file object.')

    raw_content = file_object.read()
    if isinstance(raw_content, bytes):
      try:
        raw_content = raw_content.decode()
      except ValueError:
        pass

    self.header = self.GetHeader(raw_content)
    self.content = self.GetContent(raw_content)


class IpsParser(interface.FileEntryParser):
  """Parses ips formatted log files."""

  NAME = 'ips'
  DATA_FORMAT = 'ips log file'

  _plugin_classes = {}

  def _ParseFileEntryWithPlugin(
      self, parser_mediator, plugin, ips_file, display_name):
    """Parses an ips log  file entry with a specific plugin.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      plugin (IpsPLlugin): ips parser plugin.
      ips_file (IpsFile): ips file.
      display_name (str): display name.
    """
    required_keys_exists = plugin.CheckRequiredKeys(ips_file)

    if not required_keys_exists:
      logger.debug('Skipped parsing file: {0:s} with plugin: {1:s}'.format(
          display_name, plugin.NAME))
      return

    logger.debug('Parsing file: {0:s} with plugin: {1:s}'.format(
        display_name, plugin.NAME))

    try:
      plugin.UpdateChainAndProcess(parser_mediator, ips_file=ips_file)

    except Exception as exception:  # pylint: disable=broad-except
      parser_mediator.ProduceExtractionWarning((
          'plugin: {0:s} unable to parse ips file with error: '
          '{1!s}').format(plugin.NAME, exception))

  def ParseFileEntry(self, parser_mediator, file_entry):
    """Parses an ips formatted log file entry.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_entry (dfvfs.FileEntry): file entry to be parsed.
    """
    ips_file = IpsFile()
    file_object = file_entry.GetFileObject()

    display_name = parser_mediator.GetDisplayName()

    try:
      ips_file.Open(file_object)

    except ValueError as exception:
      parser_mediator.ProduceExtractionWarning(
          '[{0:s}]unable to parse file: {1:s} with error: {2!s}'.format(
              self.NAME, display_name, exception))
      return

    if ips_file.header and ips_file.content:
      try:
        for plugin in self._plugins:
          self._ParseFileEntryWithPlugin(
              parser_mediator, plugin, ips_file, display_name)

      except Exception as exception:  # pylint: disable=broad-except
        parser_mediator.ProduceExtractionWarning((
            'plugin: {0:s} unable to parse ips file with error: '
            '{1!s}').format(plugin.NAME, exception))


manager.ParsersManager.RegisterParser(IpsParser)
