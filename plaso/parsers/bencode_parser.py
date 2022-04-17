# -*- coding: utf-8 -*-
"""Parser for bencoded files."""

import os
import re

import bencode

from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager


class BencodeValues(object):
  """Bencode values."""

  def __init__(self, decoded_values):
    """Initializes bencode values.

    Args:
      decoded_values (collections.OrderedDict[bytes|str, object]): decoded
          values.
    """
    super(BencodeValues, self).__init__()
    self._decoded_values = decoded_values

  def GetDecodedValue(self, name):
    """Retrieves a decoded value.

    Args:
      name (str): name of the value.

    Returns:
      object: decoded value or None if not available.
    """
    value = self._decoded_values.get(name, None)
    if value is None:
      # Work-around for issue in bencode 3.0.1 where keys are bytes.
      name_as_byte_stream = name.encode('utf-8')
      value = self._decoded_values.get(name_as_byte_stream, None)

    if isinstance(value, bytes):
      # Work-around for issue in bencode 3.0.1 where string values are bytes.
      value = value.decode('utf-8')

    return value


class BencodeFile(object):
  """Bencode file.

  Attributes:
    decoded_values (collections.OrderedDict[bytes|str, object]]): decoded
        values.
  """

  def __init__(self):
    """Initializes a bencode file."""
    super(BencodeFile, self).__init__()
    self._key_names = set()
    self.decoded_values = None

  @property
  def keys(self):
    """set[str]: names of all the keys."""
    return self._key_names

  def Close(self):
    """Closes the file."""
    self.decoded_values = None

  def GetDecodedValue(self, name):
    """Retrieves a decoded value.

    Args:
      name (str): name of the value.

    Returns:
      object: decoded value or None if not available.
    """
    bencoded_values = BencodeValues(self.decoded_values)
    return bencoded_values.GetDecodedValue(name)

  def GetDecodedValues(self):
    """Retrieves the decoded values.

    Yields:
      tuple[str, object]: name and decoded value.
    """
    for key, value in self.decoded_values.items():
      if isinstance(key, bytes):
        # Work-around for issue in bencode 3.0.1 where keys are bytes.
        key = key.decode('utf-8')

      yield key, value

  def Open(self, file_object):
    """Opens a bencode file.

    Args:
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      IOError: if the file-like object cannot be read.
      OSError: if the file-like object cannot be read.
      ValueError: if the file-like object is missing.
    """
    if not file_object:
      raise ValueError('Missing file object.')

    file_object.seek(0, os.SEEK_SET)

    try:
      self.decoded_values = bencode.bread(file_object)
    except bencode.BencodeDecodeError as exception:
      raise IOError(exception)

    self._key_names = set()
    for key in self.decoded_values.keys():
      if isinstance(key, bytes):
        # Work-around for issue in bencode 3.0.1 where keys are bytes.
        key = key.decode('utf-8')

      self._key_names.add(key)


class BencodeParser(interface.FileObjectParser):
  """Parser for bencoded files."""

  NAME = 'bencode'
  DATA_FORMAT = 'Bencoded file'

  # Regex match for a bencode dictionary followed by a field size.
  _BENCODE_RE = re.compile(b'd[0-9]')

  _plugin_classes = {}

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a bencoded file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    header_data = file_object.read(2)
    if not self._BENCODE_RE.match(header_data):
      raise errors.WrongParser('Not a valid Bencoded file.')

    bencode_file = BencodeFile()

    try:
      bencode_file.Open(file_object)
    except IOError as exception:
      display_name = parser_mediator.GetDisplayName()
      raise errors.WrongParser(
          '[{0:s}] unable to parse file: {1:s} with error: {2!s}'.format(
              self.NAME, display_name, exception))

    if not bencode_file.decoded_values:
      parser_mediator.ProduceExtractionWarning('missing decoded Bencode values')
      return

    try:
      for plugin in self._plugins:
        if parser_mediator.abort:
          break

        file_entry = parser_mediator.GetFileEntry()
        display_name = parser_mediator.GetDisplayName(file_entry)

        if not plugin.CheckRequiredKeys(bencode_file):
          logger.debug('Skipped parsing file: {0:s} with plugin: {1:s}'.format(
              display_name, plugin.NAME))
          continue

        logger.debug('Parsing file: {0:s} with plugin: {1:s}'.format(
            display_name, plugin.NAME))

        try:
          plugin.UpdateChainAndProcess(
              parser_mediator, bencode_file=bencode_file)

        except Exception as exception:  # pylint: disable=broad-except
          parser_mediator.ProduceExtractionWarning((
              'plugin: {0:s} unable to parse Bencode file with error: '
              '{1!s}').format(plugin.NAME, exception))

    finally:
      bencode_file.Close()


manager.ParsersManager.RegisterParser(BencodeParser)
