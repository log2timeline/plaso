 -*- coding: utf-8 -*-
"""This file contains a parser for Android logcat output."""

import pyparsing

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import logger
from plaso.parsers import manager
from plaso.parsers import text_parser


class AndroidLogcatEventData(events.EventData):
  """Android logcat event data.
  
  Attributes:
    message (str): the log message.
    pid (int): process identifier (PID) that created the logcat line.
    priority (str): a character in the set {V, D, I, W, E, F, S}, which is 
        ordered from lowest to highest priority.
    tag (str): the tag that indicates the system component from which the 
        logcat line originates.
    tid (int): thread identifier (TID) that created the logcat line.
  """

  DATA_TYPE = 'android:logcat'

  def __init__(self):
    """Initializes event data."""
    super(AndroidLogcatEventData, self).__init__(data_type=self.DATA_TYPE)
    self.message = None
    self.pid = None
    self.priority = None
    self.tag = None
    self.tid = None


class AndroidLogcatParser(text_parser.PyparsingSingleLineTextParser):
  """Parser for Android logcat output."""

  NAME = 'android_logcat'
  DATA_FORMAT = 'Android Logcat output'

  _ENCODING = 'utf-8'

  _ANDROID_DATE_GROUP = pyparsing.Combine(
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('-') +
      pyparsing.Word(pyparsing.nums, exact=2))
  
  _ANDROID_TIME_GROUP = pyparsing.Combine(
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal(':') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal(':') +
      pyparsing.Word(pyparsing.nums, exact=2) + pyparsing.Literal('.') +
      pyparsing.Word(pyparsing.nums, exact=3))

  _ANDROID_THREADTIME_LINE = (
    _ANDROID_DATE_GROUP.setResultsName('date') +
    _ANDROID_TIME_GROUP.setResultsName('time') +
    pyparsing.Word(pyparsing.nums).setsResultsName('pid') + 
    pyparsing.Literal('-') +
    pyparsing.Word(pyparsing.nums).setResultsName('tid') +
    pyparsing.Literal('/') + 
    pyparsing.Word('VDIWEFS', exact=1).setResultsName('tag') +
    pyparsing.Word(pyparsing.letters, exact=1).setResultsName('priority') +
    pyparsing.Literal('/') +
    pyparsing.restOfLine.setResultsName('message'))

  LINE_STRUCTURES = [
    ('threadtime_line', _ANDROID_THREADTIME_LINE)
  ]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a matching entry.
    
    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
        and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): elements parsed from the file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))
      
    if key == 'threadtime_line':
      event_data = AndroidLogcatEventData()
      event_data.message = self._GetValueFromStructure(structure, 'message')
      event_data.pid = self._GetValueFromStructure(structure, 'pid')
      event_data.priority = self._GetValueFromStructure(structure, 'priority')
      event_data.tag = self._GetValueFromStructure(structure, 'tag')
      event_data.tid = self._GetValueFromStructure(structure, 'tid')
