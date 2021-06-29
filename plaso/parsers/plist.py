# -*- coding: utf-8 -*-
"""Parser for binary and text Property List (plist) files."""

import binascii
import plistlib

from xml.parsers import expat

from plaso.lib import errors
from plaso.lib import specification
from plaso.parsers import interface
from plaso.parsers import logger
from plaso.parsers import manager


class PlistParser(interface.FileObjectParser):
  """Parser for binary and text Property List (plist) files."""

  NAME = 'plist'
  DATA_FORMAT = 'Property list (plist) file'

  # 50MB is 10x larger than any plist file seen to date.
  _MAXIMUM_PLIST_FILE_SIZE = 50000000

  _UTF16BE_BYTE_ORDER_MARK = b'\xfe\xff'
  _UTF16LE_BYTE_ORDER_MARK = b'\xff\xfe'
  _UTF32BE_BYTE_ORDER_MARK = b'\x00\x00\xfe\xff'
  _UTF32LE_BYTE_ORDER_MARK = b'\xff\xfe\x00\x00'
  _UTF8_BYTE_ORDER_MARK = b'\xef\xbb\xbf'

  _plugin_classes = {}

  def _CheckByteOrderMark(self, plist_data):
    """Determines if the plist data starts with a byte-order-mark.

    Args:
      plist_data (bytes): plist data.

    Returns:
      tuple: containing:

        int: size of the byte-order-mark or 0 if no byte-order-mark was
            detected.
        str: encoding or ascii if no byte-order-mark was detected.
    """
    if plist_data.startswith(self._UTF32BE_BYTE_ORDER_MARK):
      return 4, 'utf-32-be'

    if plist_data.startswith(self._UTF32LE_BYTE_ORDER_MARK):
      return 4, 'utf-32-le'

    if plist_data.startswith(self._UTF16BE_BYTE_ORDER_MARK):
      return 2, 'utf-16-be'

    if plist_data.startswith(self._UTF16LE_BYTE_ORDER_MARK):
      return 2, 'utf-16-le'

    if plist_data.startswith(self._UTF8_BYTE_ORDER_MARK):
      return 3, 'utf-8'

    return 0, 'ascii'

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: a format specification or None if not available.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(b'bplist', offset=0)
    return format_specification

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

    if file_size > self._MAXIMUM_PLIST_FILE_SIZE:
      raise errors.UnableToParseFile(
          'File size: {0:d} bytes is larger than 50 MB.'.format(file_size))

    plist_data = file_object.read()

    has_leading_whitespace = False

    is_binary_plist = plist_data.startswith(b'bplist0')
    if not is_binary_plist:
      byte_order_mark_size, encoding = self._CheckByteOrderMark(plist_data)

      xml_signature = '<?xml '.encode(encoding)
      is_xml = plist_data[byte_order_mark_size:].startswith(xml_signature)
      if not is_xml:
        # Preserve the byte-order-mark for plistlib.
        plist_data = b''.join([
            plist_data[:byte_order_mark_size],
            plist_data[byte_order_mark_size:].lstrip()])
        is_xml = plist_data[byte_order_mark_size:].startswith(xml_signature)
        has_leading_whitespace = is_xml

      if is_xml:
        plist_footer = '</plist>'.encode(encoding)
        plist_data = plist_data.rstrip()

        if not plist_data.endswith(plist_footer):
          raise errors.UnableToParseFile(
              'Unable to parse XML plist with error: missing plist XML root '
              'element.')

    try:
      top_level_object = plistlib.loads(plist_data)

    except (AttributeError, binascii.Error, expat.ExpatError,
            plistlib.InvalidFileException) as exception:
      raise errors.UnableToParseFile(
          'Unable to parse plist with error: {0!s}'.format(exception))

    except (LookupError, ValueError) as exception:
      # LookupError will be raised in cases where the plist is an XML file
      # that contains an unsupported encoding.
      # ValueError will be raised in cases where the plist is an XML file
      # that contains an unsupported date and time value.
      parser_mediator.ProduceExtractionWarning(
          'unable to parse XML plist with error: {0!s}'.format(exception))
      return

    if not top_level_object:
      # Do not produce an extraction warning for a binary plist without a top
      # level object.
      if not is_binary_plist:
        parser_mediator.ProduceExtractionWarning((
            'unable to parse XML plist file with error: missing top level '
            'object'))
      return

    if has_leading_whitespace:
      parser_mediator.ProduceExtractionWarning(
          'XML plist file with leading whitespace')

    filename_lower_case = filename.lower()

    try:
      top_level_keys = set(top_level_object.keys())
    except AttributeError as exception:
      raise errors.UnableToParseFile(
          'Unable to parse top level keys of: {0:s} with error: {1!s}.'.format(
              filename, exception))

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

      file_entry = parser_mediator.GetFileEntry()
      display_name = parser_mediator.GetDisplayName(file_entry)

      if (not path_filter_match or
          not top_level_keys.issuperset(plugin.PLIST_KEYS)):
        logger.debug('Skipped parsing file: {0:s} with plugin: {1:s}'.format(
            display_name, plugin.NAME))
        continue

      logger.debug('Parsing file: {0:s} with plugin: {1:s}'.format(
          display_name, plugin.NAME))

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
