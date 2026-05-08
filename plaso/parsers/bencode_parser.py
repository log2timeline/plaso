"""Parser for bencoded files."""

import os
import re

import bencode

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager


class BencodeValues:
  """Bencode values."""

  def __init__(self, decoded_values):
    """Initializes bencode values.

    Args:
      decoded_values (collections.OrderedDict[bytes|str, object]): decoded
          values.
    """
    super().__init__()
    self._decoded_values = decoded_values

  def GetDateTimeValue(self, name):
    """Retrieves a date and time value.

    Args:
      name (str): name of the value.

    Returns:
      dfdatetime.PosixTime: date and time or None if not available.
    """
    timestamp = self.GetDecodedValue(name)
    if not timestamp:
      return None

    return dfdatetime_posix_time.PosixTime(timestamp=timestamp)

  def GetDecodedValue(self, name):
    """Retrieves a decoded value.

    Args:
      name (str): name of the value.

    Returns:
      object: decoded value or None if not available.
    """
    value = self._decoded_values.get(name)
    if value is None:
      # Work-around for issue in bencode 3.0.1 where keys are bytes.
      name_as_byte_stream = name.encode('utf-8')
      value = self._decoded_values.get(name_as_byte_stream)

    if isinstance(value, bytes):
      # Work-around for issue in bencode 3.0.1 where string values are bytes.
      value = value.decode('utf-8')

    return value

  def GetValues(self):
    """Retrieves the values.

    Yields:
      tuple[str, object]: name and decoded value.
    """
    for key, value in self._decoded_values.items():
      if isinstance(key, bytes):
        # Work-around for issue in bencode 3.0.1 where keys are bytes.
        key = key.decode('utf-8')

      yield key, value


class BencodeFile:
  """Bencode file."""

  def __init__(self):
    """Initializes a bencode file."""
    super().__init__()
    self._decoded_values = None
    self._key_names = set()

  @property
  def keys(self):
    """Set[str]: names of all the keys."""
    return self._key_names

  def Close(self):
    """Closes the file."""
    self._decoded_values = None

  def GetValues(self):
    """Retrieves the values in the root of the bencode file.

    Returns:
      BencodeValues: values.
    """
    return BencodeValues(self._decoded_values)

  def IsEmpty(self):
    """Determines if the bencode file has no values (is empty).

    Returns:
      bool: True if the bencode file is empty, False otherwise.
    """
    return not self._decoded_values

  def Open(self, file_object):
    """Opens a bencode file.

    Args:
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      OSError: if the file-like object cannot be read.
      ValueError: if the file-like object is missing.
    """
    if not file_object:
      raise ValueError('Missing file object.')

    file_object.seek(0, os.SEEK_SET)

    try:
      self._decoded_values = bencode.bread(file_object)
    except bencode.BencodeDecodeError as exception:
      raise OSError(exception)

    self._key_names = set()
    for key in self._decoded_values.keys():
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

    display_name = parser_mediator.GetDisplayName()
    bencode_file = BencodeFile()

    try:
      bencode_file.Open(file_object)
    except OSError as exception:
      raise errors.WrongParser(
          f'[{self.NAME:s}] unable to parse file: {display_name:s} '
          f'with error: {exception!s}')

    if bencode_file.IsEmpty():
      parser_mediator.ProduceExtractionWarning('missing decoded Bencode values')
      return

    try:
      for plugin_name, plugin in self._plugins_per_name.items():
        if parser_mediator.abort:
          break

        profiling_name = '/'.join([self.NAME, plugin.NAME])

        parser_mediator.SampleFormatCheckStartTiming(profiling_name)

        try:
          result = plugin.CheckRequiredKeys(bencode_file)
        finally:
          parser_mediator.SampleFormatCheckStopTiming(profiling_name)

        if not result:
          logger.debug(
              f'Skipped parsing file: {display_name:s} with plugin: '
              f'{plugin_name:s}')
          continue

        logger.debug(
            f'Parsing file: {display_name:s} with plugin: {plugin_name:s}')

        parser_mediator.SampleStartTiming(profiling_name)

        try:
          plugin.UpdateChainAndProcess(
              parser_mediator, bencode_file=bencode_file)

        except Exception as exception:  # pylint: disable=broad-except
          parser_mediator.ProduceExtractionWarning((
              f'plugin: {plugin_name:s} unable to parse Bencode file with '
              f'error: {exception!s}'))

        finally:
          parser_mediator.SampleStopTiming(profiling_name)

    finally:
      bencode_file.Close()


manager.ParsersManager.RegisterParser(BencodeParser)
