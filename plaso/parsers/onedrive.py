# -*- coding: utf-8 -*-
"""Parser for OneDrive Log (ODL/ODLGZ) files.

Reference: https://forensics.wiki/microsoft_onedrive/
"""

import base64
import io
import json
import os
import re
import zlib

import pycaes

from dfdatetime import posix_time as dfdatetime_posix_time

from dfvfs.helpers import text_file as dfvfs_text_file

from plaso.containers import events
from plaso.lib import dtfabric_helper
from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import manager


class OneDriveLogEvent(events.EventData):
  """OneDrive log event data.

  Attributes:
    code_filename (str): code filename.
    code_function_name (str): code function name.
    decoded_parameters (str): decoded (and decrypted) parameters.
    raw_parameters (str): the raw parameters encoded as a hexadecimal
        formatted string.
    recorded_time (dfdatetime.DateTimeValues): date and time the entry was
        recorded.
  """

  DATA_TYPE = 'windows:onedrive:log'

  def __init__(self):
    """Initializes event data."""
    super(OneDriveLogEvent, self).__init__(data_type=self.DATA_TYPE)
    self.code_filename = None
    self.code_function_name = None
    self.decoded_parameters = None
    self.raw_parameters = None
    self.recorded_time = None


class OneDriveLogFileParser(
    interface.FileEntryParser, dtfabric_helper.DtFabricHelper):
  """Parser for OneDrive log files."""

  NAME = 'onedrive_log'
  DATA_FORMAT = 'OneDrive Log file'

  BLOCK_SIGNATURE = b'\xcc\xdd\xee\xff\x00\x00\x00\x00'
  COMPRESSED_BLOCK_SIGNATURE = b'\x1f\x8b\x08\x00\x00\x00\x00\x00'

  _AES_IV = b'\x00' * 16
  _AES_KEY_LENGTH = 32
  _BASE64_ALPHABET = (
      'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789_-')
  _DEFINITION_FILE = os.path.join(
      os.path.dirname(__file__), 'onedrive.yaml')
  _DELIMITERS = [r'%', r'\\', r'/', r'://', r'\?', r':', r'\.']
  _DELIMITERS_REGEX_PATTERN = '({0:s})'.format('|'.join(_DELIMITERS))
  _DELIMITERS_REGEX = re.compile(_DELIMITERS_REGEX_PATTERN)
  _FIRST_DATA_BLOCK_OFFSET = 256
  _GENERAL_KEYSTORE_FILE_NAME = 'general.keystore'
  _MAXIMUM_FILE_SIZE = 5 * 1024 * 1024
  _OBFUSCATED_STRING_MAP_FILE_NAME = 'ObfuscationStringMap.txt'

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: format specification.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'EBFGONED', offset=0)
    return format_specification

  def _ParseObfuscatedStringMap(
      self, obfuscated_string_map_entry):
    """Parses the ObfuscatedStringMap.txt file.

    ObfuscatedStringMap.txt is a UTF-16 little-endian encoded text file where
    each line contains a tab delimited mapping between an obfuscated string
    value (as read from a OneDrive log file) and its original string value.

    Args:
      obfuscated_string_map_entry (dfvfs.FileEntry): the file entry of the
          ObfuscatedStringMap.txt file.

    Returns:
      dict[str, str]: a mapping of an obfuscated string value to its
          original string value.
    """
    file_object = obfuscated_string_map_entry.GetFileObject()

    obfuscated_string_map = {}
    with dfvfs_text_file.TextFile(
        file_object, encoding='utf-16-le') as obfuscated_text_file:
      for line in obfuscated_text_file.readlines():
        line_tokens = line.rstrip().split('\t')
        if len(line_tokens) == 2:
          obfuscated_string, original_string = line_tokens
          if obfuscated_string not in obfuscated_string_map:
            obfuscated_string_map[obfuscated_string] = original_string

    return obfuscated_string_map

  def _ParseGeneralKeyStore(self, file_entry, parser_mediator):
    """Parses the general.keystore file.

    Args:
      file_entry (dfvfs.FileEntry): the file entry of the general.keystore file.
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.

    Returns:
      Optional[bytes]: the parsed and base64-decoded AES key or None if the
          general.keystore file could not be parsed as JSON or does not contain
          a valid Key value.
    """
    file_object = file_entry.GetFileObject()

    # Note that _MAXIMUM_FILE_SIZE prevents this read to become too large.
    general_keystore_data = file_object.read()

    json_data = json.loads(general_keystore_data)
    if not json_data or not isinstance(json_data, list):
      parser_mediator.ProduceExtractionWarning(
          'Unable to parse OneDrive keystore file: {0:s}'.format(
              file_entry.name))
      return None

    key = json_data[0].get('Key', None)
    if not key:
      parser_mediator.ProduceExtractionWarning(
          'OneDrive keystore file: {0:s} does not contain a key value.'.format(
              file_entry.name))
      return None

    decoded_key = base64.b64decode(key)

    if len(decoded_key) != self._AES_KEY_LENGTH:
      parser_mediator.ProduceExtractionWarning((
          'OneDrive keystore file: {0:s} does not contain a key value of '
          'size: 32.').format(file_entry.name))
      return None

    return decoded_key

  def _DeobfuscateStrings(self, extracted_strings, obfuscated_string_map):
    """Deobfuscate strings extracted from OneDrive logs.

    Args:
      extracted_strings (list[str]): strings extracted from OneDrive log files.
      obfuscated_string_map (dict[str, str]): the parsed obfuscated string map.

    Returns:
      list[str]: the list of extracted strings, replaced by their true value if
          it exists in the obfuscated string map.
    """
    if not obfuscated_string_map:
      return extracted_strings

    deobfuscated_strings = []

    for extracted_string in extracted_strings:
      extracted_string_tokens = self._DELIMITERS_REGEX.split(extracted_string)
      output_string_parts = []

      for extracted_string_token in extracted_string_tokens:
        if extracted_string_token in self._DELIMITERS:
          output_string_parts.append(extracted_string_token)
        else:
          deobfuscated_string_token = obfuscated_string_map.get(
              extracted_string_token, extracted_string_token)
          output_string_parts.append(deobfuscated_string_token)

      deobfuscated_strings.append(''.join(output_string_parts))

    return deobfuscated_strings

  def _DecryptAES(self, aes_key, encrypted_data):
    """Decrypt AES-CBC encrypted data.

    Args:
      aes_key (bytes): the AES key.
      data (bytes): AES-CBC encrypted data.

    Returns:
      bytes: decrypted data.
    """
    aes_context = pycaes.context()
    aes_context.set_key(pycaes.crypt_modes.DECRYPT, aes_key)
    return pycaes.crypt_cbc(
        aes_context, pycaes.crypt_modes.DECRYPT,
        self._AES_IV, encrypted_data)

  def _DecryptStrings(self, parser_mediator, aes_key, extracted_strings):
    """Decrypt strings extracted from OneDrive logs.

    The encrypted strings are stored as follows:
    * split into tokens using delimiters ('%', '\', '/', '://', '?', ':', '.')
    * URL safe base64 encoded
    * encrypted using AES-CBC where the AES key is parsed from the
      general.keystore file and the IV is 16 zero byte values
    * padded using PKCS#7
    * encoded in UTF-16 little-endian

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      aes_key (bytes): the AES key.
      extracted_strings (list[str]): strings extracted from OneDrive log files.

    Returns:
      list[str]: the decrypted strings.
    """
    decrypted_strings = []

    for extracted_string in extracted_strings:
      tokens = self._DELIMITERS_REGEX.split(extracted_string)

      output_string_parts = []
      for token in tokens:
        if token in self._DELIMITERS:
          output_string_parts.append(token)
          continue

        token_size = len(token)

        # The minimum block size of base64 encoded AES-CBC is 22 bytes.
        if token_size < 22:
          output_string_parts.append(token)
          continue

        if not all(character in self._BASE64_ALPHABET for character in token):
          output_string_parts.append(token)
          continue

        base64_padding_size = token_size % 4
        if base64_padding_size == 1:
          output_string_parts.append(token)
          continue

        if base64_padding_size > 1:
          base64_padding = '=' * base64_padding_size
          token = ''.join([token, base64_padding])

        ciphertext = base64.urlsafe_b64decode(token)

        if len(ciphertext) % 16:
          output_string_parts.append(token)
          continue

        plaintext = self._DecryptAES(aes_key, ciphertext)

        try:
          data = self._RemovePKCS7Padding(plaintext, block_size=128)
        except ValueError as exception:
          parser_mediator.ProduceExtractionWarning(
              'unable to remove PKCS#7 padding with error: {0!s}'.format(
                  exception))

          output_string_parts.append(token)
          continue

        try:
          decoded_string = data.decode('utf-16-le')
        except UnicodeError as exception:
          parser_mediator.ProduceExtractionWarning(
              'unable to decode string with error: {0!s}'.format(exception))

          output_string_parts.append(token)
          continue

        output_string_parts.append(decoded_string)

      decrypted_strings.append(''.join(output_string_parts))

    return decrypted_strings

  def _ExtractStringsFromParameters(self, buffer):
    """Extracts strings from raw parameter bytes.

    Args:
      buffer (bytearray): the buffer.

    Returns:
      list[str]: strings parsed from the raw parameter bytes.
    """
    pascal_string_map = self._GetDataTypeMap('pascal_string')

    parse_offset = 0
    strings_array = []

    while parse_offset < len(buffer):
      try:
        pascal_string = self._ReadStructureFromByteStream(
            buffer[parse_offset:], 0, pascal_string_map)
      except errors.ParseError:
        parse_offset += 4
        continue

      strings_array.append(pascal_string.value)
      parse_offset += 4 + pascal_string.size

    return strings_array

  def _ProcessRawParameters(
      self, parser_mediator, raw_parameters_data, aes_key,
      obfuscated_string_map):
    """Processes (extracts and decrypts/deobfuscates) the raw parameters.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      raw_parameters_data (bytes): the raw parameters data from a log entry.
      aes_key (bytes): the AES key used to decrypt strings, or None if there
          is no parsed AES key.
      obfuscated_string_map (dict[str, str]): the obfuscated string map used
          to deobfuscate strings, or None if there is no parsed string mapping.

    Returns:
      list[str]: a list of strings that were parsed from the raw parameters.
    """
    extracted_strings = self._ExtractStringsFromParameters(raw_parameters_data)
    if aes_key:
      extracted_strings = self._DecryptStrings(
          parser_mediator, aes_key, extracted_strings)

    if obfuscated_string_map:
      extracted_strings = self._DeobfuscateStrings(
          extracted_strings, obfuscated_string_map)

    return extracted_strings

  def _RemovePKCS7Padding(self, padded_data, block_size=8):
    """Validates and removes PKCS#7 padding.

    Args:
      padded_data (bytes): data with PKCS#7 padding.
      block_size (Optional[int]): block size.

    Returns:
      bytes: data without PKCS#7 padding.

    Raises:
      ValueError: if the padding is invalid.
    """
    if padded_data:
      padding_size = padded_data[-1]
    else:
      padding_size = 0

    if padding_size <= 0 or padding_size > block_size:
      raise ValueError(
          'Invalid padding size: {0:d} value out of bounds'.format(
              padding_size))

    for byte_index in range(2, padding_size + 1):
      check_padding_size = padded_data[-byte_index]
      if check_padding_size != padding_size:
        raise ValueError((
            'Mismatch in padding size: {0:d} and: {1:d} at byte index: '
            '{2:d}').format(padding_size, check_padding_size, -byte_index))

    return padded_data[:-padding_size]

  def ParseFileEntry(self, parser_mediator, file_entry):
    """Parses a OneDrive Log file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_entry (dfvfs.FileEntry): file entry.

    Raises:
      ParseError: when a log cannot be decompressed.
      WrongParser: when the file cannot be parsed.
    """
    onedrivelog_file_header_map = self._GetDataTypeMap(
        'onedrivelog_file_header')

    file_object = file_entry.GetFileObject()

    try:
      _, data_size = self._ReadStructureFromFileObject(
          file_object, 0, onedrivelog_file_header_map)
    except (ValueError, errors.ParseError) as exception:
      raise errors.WrongParser(
          'Unable to parse OneDrive Log file header with error: {0!s}'.format(
              exception))

    # skip to the first data block offset and check the signature
    file_object.seek(self._FIRST_DATA_BLOCK_OFFSET, os.SEEK_SET)
    data_block_signature = file_object.read(8)

    if data_block_signature == self.COMPRESSED_BLOCK_SIGNATURE:
      file_object.seek(self._FIRST_DATA_BLOCK_OFFSET, os.SEEK_SET)

      # Note that _MAXIMUM_FILE_SIZE prevents this read to become too large.
      raw_data_block = file_object.read()
      try:
        raw_data_block = zlib.decompress(
            raw_data_block, wbits = zlib.MAX_WBITS | 16)
      except zlib.error as zlib_error:
        raise errors.ParseError(
            'Error decompressing data block: {0!s}'.format(str(zlib_error)))

      data_block_stream = io.BytesIO(raw_data_block)
      data_block_size = len(data_block_stream.getbuffer())
      stream_offset = 0

    elif data_block_signature == self.BLOCK_SIGNATURE:
      file_object.seek(self._FIRST_DATA_BLOCK_OFFSET, os.SEEK_SET)
      data_block_stream = file_object
      data_block_size = file_entry.size
      stream_offset = 256

    else:
      raise errors.ParseError('Invalid signature found.')

    parent_file_entry = file_entry.GetParentFileEntry()

    obfuscated_string_map_file_entry = parent_file_entry.GetSubFileEntryByName(
        self._OBFUSCATED_STRING_MAP_FILE_NAME)
    if obfuscated_string_map_file_entry:
      obfuscated_string_map = self._ParseObfuscatedStringMap(
          obfuscated_string_map_file_entry)
    else:
      obfuscated_string_map = None

    aes_key_file_entry = parent_file_entry.GetSubFileEntryByName(
        self._GENERAL_KEYSTORE_FILE_NAME)
    if aes_key_file_entry:
      aes_key = self._ParseGeneralKeyStore(aes_key_file_entry, parser_mediator)
    else:
      aes_key = None

    odl_data_block_header_map = self._GetDataTypeMap('odl_data_block_header')
    odl_data_block_map = self._GetDataTypeMap('odl_data_block')

    while (stream_offset + odl_data_block_header_map.GetSizeHint() <
        data_block_size):
      try:
        odl_data_block_header, header_data_size = (
            self._ReadStructureFromFileObject(
                data_block_stream, stream_offset, odl_data_block_header_map))
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to parse data block header at stream offset: 0x{0:08x} '
            'with error: {1!s}').format(stream_offset, exception))
        return

      stream_offset += header_data_size

      try:
        odl_data_block, data_size = self._ReadStructureFromFileObject(
            data_block_stream, stream_offset, odl_data_block_map)
      except (ValueError, errors.ParseError) as exception:
        parser_mediator.ProduceExtractionWarning((
            'unable to parse data block at stream offset: 0x{0:08x} with '
            'error: {1!s}').format(stream_offset, exception))
        return

      # read the raw function parameter data
      stream_offset += data_size
      raw_parameters_size = odl_data_block_header.data_size - data_size
      raw_parameters_data = data_block_stream.read(raw_parameters_size)
      stream_offset += raw_parameters_size

      extracted_strings = self._ProcessRawParameters(
          parser_mediator, raw_parameters_data, aes_key, obfuscated_string_map)

      event_data = OneDriveLogEvent()
      event_data.code_filename = odl_data_block.code_filename.decode('utf-8')
      event_data.code_function_name = odl_data_block.code_function_name.decode(
          'utf-8')

      event_data.decoded_parameters = extracted_strings
      event_data.raw_parameters = raw_parameters_data.hex()
      event_data.recorded_time = dfdatetime_posix_time.PosixTimeInMilliseconds(
          timestamp=odl_data_block_header.timestamp)
      parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(OneDriveLogFileParser)
