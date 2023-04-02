# -*- coding: utf-8 -*-
"""Base parser for line-based JSON (JSON-L) log formats."""

import json

from json import decoder as json_decoder

from dfvfs.helpers import text_file

from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class JSONLParser(interface.FileObjectParser):
  """Base parser for line-based JSON (JSON-L) log formats."""

  NAME = 'jsonl'
  DATA_FORMAT = 'JSON-L log file'

  _ENCODING = 'utf-8'

  _MAXIMUM_LINE_LENGTH = 64 * 1024

  _plugin_classes = {}

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a line-based JSON (JSON-L) log file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    encoding = self._ENCODING
    if not encoding:
      encoding = parser_mediator.GetCodePage()

    # Use strict encoding error handling in the verification step so that
    # a JSON-L parser does not generate extraction warning for encoding errors
    # of unsupported files.
    text_file_object = text_file.TextFile(file_object, encoding=encoding)

    try:
      line = text_file_object.readline(size=self._MAXIMUM_LINE_LENGTH)
    except UnicodeDecodeError:
      raise errors.WrongParser('Not a JSON-L file or encoding not supported.')

    if not line:
      raise errors.WrongParser('Not a JSON-L file.')

    line = line.strip()
    if not line or (line[0] != '{' and line[-1] != '}'):
      raise errors.WrongParser(
          'Not a JSON-L file, missing opening and closing braces.')

    try:
      json_dict = json.loads(line)
    except json_decoder.JSONDecodeError:
      raise errors.WrongParser('Not a JSON-L file, unable to decode JSON.')

    if not json_dict:
      raise errors.WrongParser('Not a JSON-L file, missing JSON.')

    for plugin_name, plugin in self._plugins_per_name.items():
      if parser_mediator.abort:
        break

      profiling_name = '/'.join([self.NAME, plugin.NAME])

      parser_mediator.SampleFormatCheckStartTiming(profiling_name)

      try:
        result = plugin.CheckRequiredFormat(json_dict)
      finally:
        parser_mediator.SampleFormatCheckStopTiming(profiling_name)

      if not result:
        continue

      parser_mediator.SampleStartTiming(profiling_name)

      try:
        plugin.UpdateChainAndProcess(
            parser_mediator, file_object=file_object)

      except Exception as exception:  # pylint: disable=broad-except
        parser_mediator.ProduceExtractionWarning((
            'plugin: {0:s} unable to parse JSON-L file with error: '
            '{1!s}').format(plugin_name, exception))

      finally:
        parser_mediator.SampleStopTiming(profiling_name)


manager.ParsersManager.RegisterParser(JSONLParser)
