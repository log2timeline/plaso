# -*- coding: utf-8 -*-
"""Parser for IPS formatted log files.

These files are used by Apple in iOS (15 and later) and MacOS (12 and later).
Each file is a single event."""

import json
import re
import yaml

from yaml import scanner as yaml_scanner

from plaso.parsers import interface
from plaso.parsers import logger
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

  def _GetContent(self, raw_content):
    """Extracts content from the file.

    Args:
      raw_content (str): content of the IPS log.

    Returns:
      dict[str, object]: JSON serialized objects.
    """
    if not isinstance(raw_content, str):
      return None

    content = re.search('}\n({.+)', raw_content, re.DOTALL)
    if not content:
      return None

    try:
      structured_content = yaml.safe_load(content.group(1))
    except (AttributeError, yaml_scanner.ScannerError):
      structured_content = None

    return structured_content

  def _GetHeader(self, raw_content):
    """Extracts a header from the file.

    Agrs:
      raw_content (str): content of the IPS log.

    Returns:
      dict[str, object]: JSON serialized objects.
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
    """Opens an IPS log file.

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

    self.header = self._GetHeader(raw_content)
    self.content = self._GetContent(raw_content)


class IPSParser(interface.FileEntryParser):
  """Parses IPS formatted log files."""

  NAME = 'ips'
  DATA_FORMAT = 'IPS log file'

  _plugin_classes = {}

  def _ParseFileEntryWithPlugin(
      self, parser_mediator, plugin, ips_file, display_name):
    """Parses an IPS log file entry with a specific plugin.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      plugin (IPSPlugin): IPS parser plugin.
      ips_file (IPSFile): IPS file.
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
          'plugin: {0:s} unable to parse IPS file with error: '
          '{1!s}').format(plugin.NAME, exception))

  def ParseFileEntry(self, parser_mediator, file_entry):
    """Parses an IPS formatted log file entry.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      file_entry (dfvfs.FileEntry): file entry to be parsed.
    """
    ips_file = IPSFile()
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
            'plugin: {0:s} unable to parse IPS file with error: '
            '{1!s}').format(plugin.NAME, exception))


manager.ParsersManager.RegisterParser(IPSParser)
