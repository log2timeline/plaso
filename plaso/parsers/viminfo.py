# -*- coding: utf-8 -*-
"""Parser for viminfo files."""

import pyparsing

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import specification
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import interface


class VimInfoFileParser():
  """A viminfo file parser."""

  _HEADER_1 = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('# This viminfo file was generated by Vim ') +
      pyparsing.Word(pyparsing.nums + '.') +
      pyparsing.Suppress(pyparsing.LineEnd()))

  _HEADER_2 = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('# You may edit it if you\'re careful!') +
      pyparsing.Suppress(pyparsing.LineEnd()))

  _VERSION_HEADER = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('# Viminfo version') +
      pyparsing.Suppress(pyparsing.LineEnd()))

  _VERSION_VALUE = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('|') +
      pyparsing.Word(pyparsing.nums + ',').setResultsName('version') +
      pyparsing.Suppress(pyparsing.LineEnd()))

  _ENCODING_HEADER = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('# Value of \'encoding\' when this file was written') +
      pyparsing.Suppress(pyparsing.LineEnd()))

  _ENCODING_VALUE = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('*') +
      pyparsing.Literal('encoding=') +
      pyparsing.Word(pyparsing.alphanums + '-').setResultsName('encoding') +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      pyparsing.Suppress(pyparsing.LineEnd()))

  _PREAMBLE = (
      _HEADER_1 + _HEADER_2 + _VERSION_HEADER + _VERSION_VALUE +
      _ENCODING_HEADER + _ENCODING_VALUE)

  _HLSEARCH = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('# hlsearch on (H) or off (h):') +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Word('~/hH').setResultsName('hlsearch') +
      pyparsing.Suppress(pyparsing.LineEnd()))

  # TODO: https://github.com/vim/vim/blob/master/src/viminfo.c#L1525
  _SEARCH_PATTERN = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('# Last Search Pattern:') +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Word(pyparsing.alphanums + '~/').setResultsName(
        'search_pattern') +
      pyparsing.Suppress(pyparsing.LineEnd()))

  # TODO: https://github.com/vim/vim/blob/master/src/viminfo.c#L1525
  _SUBSTITUTE_SEARCH_PATTERN = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('# Last Substitute Search Pattern:') +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.restOfLine.setResultsName('substitute_search_pattern') +
      pyparsing.Suppress(pyparsing.LineEnd()))

  _SUBSTITUTE_STRING = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('# Last Substitute String:') +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.restOfLine.setResultsName('last_substitute_string') +
      pyparsing.Suppress(pyparsing.LineEnd()))

  _BAR_ITEM = (
      pyparsing.Suppress(pyparsing.LineStart()) +  pyparsing.Literal('|') +
      pyparsing.Word(pyparsing.nums, exact=1) + pyparsing.Suppress(',') +
      pyparsing.Word(pyparsing.nums, exact=1) + pyparsing.Suppress(',') +
      pyparsing.Word(pyparsing.nums, exact=10) +  pyparsing.Suppress(',') +
      pyparsing.Optional(pyparsing.Word(pyparsing.nums)) +
      pyparsing.Suppress(',') +
      pyparsing.restOfLine + pyparsing.Suppress(pyparsing.LineEnd()))

  _REGISTER_CONTINUATION = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('|<"') +
      pyparsing.restOfLine +
      pyparsing.Suppress(pyparsing.LineEnd()))

  _REGISTER_ITEM = (
      pyparsing.Suppress(pyparsing.LineStart()) +  pyparsing.Literal('|') +
      pyparsing.Word(pyparsing.nums) + pyparsing.Suppress(',') +
      pyparsing.Word(pyparsing.nums) + pyparsing.Suppress(',') +
      pyparsing.Word(pyparsing.nums) + pyparsing.Suppress(',') +
      pyparsing.Word(pyparsing.nums) + pyparsing.Suppress(',') +
      pyparsing.Word(pyparsing.nums) + pyparsing.Suppress(',') +
      pyparsing.Word(pyparsing.nums) + pyparsing.Suppress(',') +
      pyparsing.Word(pyparsing.nums, exact=10) + pyparsing.Suppress(',') +
      pyparsing.Group(
          pyparsing.restOfLine +
          pyparsing.Suppress(pyparsing.LineEnd()) +
          pyparsing.ZeroOrMore(_REGISTER_CONTINUATION)))

  _FILEMARK_ITEM = pyparsing.Group(
      pyparsing.Suppress(pyparsing.LineStart()) +  pyparsing.Literal('|') +
      pyparsing.Word(pyparsing.nums) + pyparsing.Suppress(',') +
      pyparsing.Word(pyparsing.nums) + pyparsing.Suppress(',') +
      pyparsing.Word(pyparsing.nums) + pyparsing.Suppress(',') +
      pyparsing.Word(pyparsing.nums) + pyparsing.Suppress(',') +
      pyparsing.Word(pyparsing.nums, exact=10) + pyparsing.Suppress(',') +
      pyparsing.restOfLine +pyparsing.Suppress(pyparsing.LineEnd()))

  _COMMAND_LINE_ITEM = pyparsing.Group(
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal(':') +
      pyparsing.restOfLine +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      _BAR_ITEM).setResultsName('command_line_items*')

  _COMMAND_LINE_HISTORY = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('# Command Line History (newest to oldest):') +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      pyparsing.ZeroOrMore(_COMMAND_LINE_ITEM))

  _SEARCH_STRING_ITEM = pyparsing.Group(
      pyparsing.Suppress(pyparsing.LineStart()) +  pyparsing.Literal('?') +
      pyparsing.restOfLine +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      _BAR_ITEM).setResultsName('search_string_items*')

  _SEARCH_STRING_HISTORY = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('# Search String History (newest to oldest):') +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      pyparsing.ZeroOrMore(_SEARCH_STRING_ITEM))

  _EXPRESSION_ITEM = pyparsing.Group(
      pyparsing.Suppress(pyparsing.LineStart()) +  pyparsing.Literal('=') +
      pyparsing.Word(pyparsing.alphas + '/:') +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      _BAR_ITEM).setResultsName('expression_history_items*')

  _EXPRESSION_HISTORY = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('# Expression History (newest to oldest):') +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      pyparsing.ZeroOrMore(_EXPRESSION_ITEM))

  _INPUT_LINE_ITEM = pyparsing.Group(
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('@') +
      pyparsing.Word(pyparsing.alphas + '/:') +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      _BAR_ITEM).setResultsName('input_line_history_items*')

  _INPUT_LINE_HISTORY = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('# Input Line History (newest to oldest):') +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      pyparsing.ZeroOrMore(_INPUT_LINE_ITEM))

  _DEBUG_LINE_ITEM = pyparsing.Group(
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('@') +
      pyparsing.Word(pyparsing.alphas + '/:') +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      _BAR_ITEM).setResultsName('debug_line_history_items*')

  _DEBUG_LINE_HISTORY = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('# Debug Line History (newest to oldest):') +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      pyparsing.ZeroOrMore(_DEBUG_LINE_ITEM))

  _REGISTERS_CONTENT = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Suppress(pyparsing.White('\t')) +
      pyparsing.restOfLine() +
      pyparsing.Suppress(pyparsing.LineEnd()))

  # http://vimdoc.sourceforge.net/htmldoc/change.html#registers
  _REGISTERS_ITEM = pyparsing.Group(
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('"') +
      pyparsing.Or([pyparsing.Word(pyparsing.nums),
                    pyparsing.Word(pyparsing.printables)]) +
      pyparsing.Suppress(pyparsing.White('\t')) +
      pyparsing.Or(['CHAR', 'LINE', 'BLOCK']) +
      pyparsing.Suppress(pyparsing.White('\t')) +
      pyparsing.Word(pyparsing.nums) + pyparsing.Suppress(pyparsing.LineEnd()) +
      pyparsing.Group(pyparsing.ZeroOrMore(_REGISTERS_CONTENT)) +
      _REGISTER_ITEM).setResultsName('registers_items*')

  _REGISTERS_HISTORY = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('# Registers:') +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      pyparsing.ZeroOrMore(_REGISTERS_ITEM))

  _FILEMARKS_ITEM = pyparsing.Group(
      pyparsing.Suppress(pyparsing.LineStart()) +  pyparsing.Literal('\'') +
      pyparsing.Word(pyparsing.nums) +
      pyparsing.Word(pyparsing.nums) +
      pyparsing.Word(pyparsing.nums) +
      pyparsing.restOfLine +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      _FILEMARK_ITEM).setResultsName('filemarks_items*')

  _FILEMARKS_HISTORY = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('# File marks:') +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      pyparsing.ZeroOrMore(_FILEMARKS_ITEM))

  _JUMPLIST_ITEM = pyparsing.Group(
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Word('-\'') +
      pyparsing.Word(pyparsing.nums) +
      pyparsing.Word(pyparsing.nums) +
      pyparsing.restOfLine +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      _FILEMARK_ITEM).setResultsName('jumplist_items*')

  _JUMPLIST_HISTORY = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('# Jumplist (newest first):') +
      pyparsing.Suppress(pyparsing.LineEnd()) +
      pyparsing.ZeroOrMore(_JUMPLIST_ITEM))

  _HISTORY_MARKS_HISTORY = (
      pyparsing.Suppress(pyparsing.LineStart()) +
      pyparsing.Literal('# History of marks within files (newest to oldest):') +
      pyparsing.Suppress(pyparsing.LineEnd()))

  VIMINFO_STRUCTURE = (
      _PREAMBLE +
      _HLSEARCH +
      _SEARCH_PATTERN +
      pyparsing.Optional(_SUBSTITUTE_SEARCH_PATTERN) +
      pyparsing.Optional(_SUBSTITUTE_STRING) +
      _COMMAND_LINE_HISTORY +
      _SEARCH_STRING_HISTORY +
      _EXPRESSION_HISTORY +
      _INPUT_LINE_HISTORY +
      _DEBUG_LINE_HISTORY +
      _REGISTERS_HISTORY +
      _FILEMARKS_HISTORY +
      _JUMPLIST_HISTORY +
      _HISTORY_MARKS_HISTORY
  ).parseWithTabs()

  def __init__(self, file_data):
    self.parsed_data = self.VIMINFO_STRUCTURE.parse_string(file_data)

  def CommandLineHistory(self):
    """Returns a list of command line history items."""
    items = []
    for i, item in enumerate(self.parsed_data.get('command_line_items', [])):
      items.append({'index': i, 'timestamp': int(item[5]), 'command': item[1]})
    return items

  def SearchStringHistory(self):
    """Returns a list of search string history items."""
    items = []
    for i, item in enumerate(self.parsed_data.get('search_string_items', [])):
      items.append(
          {'index': i, 'timestamp': int(item[5]), 'search_string': item[1]})
    return items

  def ExpressionHistory(self):
    """Returns a list of expression history items."""
    items = []
    for i, item in enumerate(self.parsed_data.get(
        'expression_history_items', [])):
      items.append(
          {'index': i, 'timestamp': int(item[5]), 'expression': item[1]})
    return items

  def InputLineHistory(self):
    """Returns a list of input line history items."""
    items = []
    for i, item in enumerate(self.parsed_data.get(
        'input_line_history_items', [])):
      items.append(
          {'index': i, 'timestamp': int(item[5]), 'input line': item[1]})
    return items

  def DebugLineHistory(self):
    """Returns a list of debug line history items."""
    items = []
    for i, item in enumerate(self.parsed_data.get(
        'debug_line_history_items', [])):
      items.append(
          {'index': i, 'timestamp': int(item[5]), 'debug line': item[1]})
    return items

  def Registers(self):
    """Returns a list of register items."""
    items = []
    for item in self.parsed_data.get('registers_items', []):
      items.append({
          'register': item[1],
          'timestamp': int(item[12]),
          'register_value': '\n'.join(item[4])})
    return items

  def Filemarks(self):
    """Returns a list of filemark items."""
    items = []
    for i, item in enumerate(self.parsed_data.get('filemarks_items', [])):
      items.append(
          {'index': i, 'timestamp': int(item[5][5]), 'filename': item[4]})
    return items

  def Jumplist(self):
    """Returns a list of jumplist items."""
    items = []
    for i, item in enumerate(self.parsed_data.get('jumplist_items', [])):
      items.append(
          {'index': i, 'timestamp': int(item[4][5]), 'filename': item[3]})
    return items


class VimInfoEventData(events.EventData):
  """VimInfo event data.

  Attributes:
    type (str): the Vim history type.
    value (str): the Vim history value.
    filename (str): the name of the file that was opened/edited.
    item_number (int): the nth item of the history type.
  """

  DATA_TYPE = 'viminfo:history'

  def __init__(self):
    """Initializes event data."""
    super(VimInfoEventData, self).__init__(data_type=self.DATA_TYPE)
    self.type = None
    self.value = None
    self.filename = None
    self.item_number = None


class VimInfoParser(interface.FileObjectParser):
  """Parses events from Viminfo files."""

  NAME = 'viminfo'
  DATA_FORMAT = 'Viminfo file'

  _ENCODING = 'utf-8'

  # 10 MiB is the maximum supported viminfo file size.
  _MAXIMUM_VIMINFO_FILE_SIZE = 10 * 1024 * 1024

  _FILENAME = '.viminfo'

  @classmethod
  def GetFormatSpecification(cls):
    """Retrieves the format specification.

    Returns:
      FormatSpecification: a format specification or None if not available.
    """
    format_specification = specification.FormatSpecification(cls.NAME)
    format_specification.AddNewSignature(
        b'# This viminfo file was generated by Vim', offset=0)
    return format_specification

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses a plist file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    filename = parser_mediator.GetFilename()
    if filename != self._FILENAME:
      raise errors.WrongParser(
          'File name: {0} does not match the expected viminfo filename'.format(
              filename))

    file_size = file_object.get_size()
    if file_size <= 0:
      raise errors.WrongParser(
          'File size: {0:d} bytes is less equal 0.'.format(file_size))

    if file_size > self._MAXIMUM_VIMINFO_FILE_SIZE:
      raise errors.WrongParser(
          'File size: {0:d} bytes is larger than 10 MiB.'.format(file_size))

    viminfo_data = file_object.read()

    try:
      file_data = viminfo_data.decode()
      viminfo_file = VimInfoFileParser(file_data=file_data)
    except pyparsing.ParseException as exception:
      parser_mediator.ProduceExtractionWarning(
          'unable to parse Viminfo file with error: {0!s}', exception)

    for item in viminfo_file.CommandLineHistory():
      event_data = VimInfoEventData()
      event_data.value = item['command']
      event_data.type = 'Command Line History'
      event_data.item_number = item['index']

      timestamp = item['timestamp']
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_RECORDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    for item in viminfo_file.SearchStringHistory():
      event_data = VimInfoEventData()
      event_data.value = item['search_string']
      event_data.type = 'Search String History'
      event_data.item_number = item['index']

      timestamp = item['timestamp']
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_RECORDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    for item in viminfo_file.ExpressionHistory():
      event_data = VimInfoEventData()
      event_data.value = item['expression']
      event_data.type = 'Expression History'
      event_data.item_number = item['index']

      timestamp = item['timestamp']
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_RECORDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    for item in viminfo_file.InputLineHistory():
      event_data = VimInfoEventData()
      event_data.value = item['input line']
      event_data.type = 'Input Line History'
      event_data.item_number = item['index']

      timestamp = item['timestamp']
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_RECORDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    for item in viminfo_file.DebugLineHistory():
      event_data = VimInfoEventData()
      event_data.value = item['debug line']
      event_data.type = 'Debug Line History'
      event_data.item_number = item['index']

      timestamp = item['timestamp']
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_RECORDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    for item in viminfo_file.Registers():
      event_data = VimInfoEventData()
      event_data.value = item['register_value']
      event_data.type = 'Register'
      event_data.item_number = item['register']

      timestamp = item['timestamp']
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_RECORDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    for item in viminfo_file.Filemarks():
      event_data = VimInfoEventData()
      event_data.filename = item['filename'].strip()
      event_data.type = 'File mark'
      event_data.item_number = item['index']

      timestamp = item['timestamp']
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_RECORDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    for item in viminfo_file.Jumplist():
      event_data = VimInfoEventData()
      event_data.filename = item['filename'].strip()
      event_data.type = 'Jumplist'
      event_data.item_number = item['index']

      timestamp = item['timestamp']
      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_RECORDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)


manager.ParsersManager.RegisterParser(VimInfoParser)