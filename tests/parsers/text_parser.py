#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains the tests for the generic text parser."""

import unittest

import pyparsing

from plaso.events import text_events
from plaso.formatters import interface as formatters_interface
from plaso.formatters import manager as formatters_manager
from plaso.formatters import mediator as formatters_mediator
from plaso.lib import errors
from plaso.lib import lexer
from plaso.lib import timelib
from plaso.parsers import text_parser

from tests.parsers import test_lib


class TestTextEvent(text_events.TextEvent):
  """Test text event."""
  DATA_TYPE = u'test:parser:text'


class TestTextEventFormatter(formatters_interface.EventFormatter):
  """Test text event formatter."""
  DATA_TYPE = u'test:parser:text'
  FORMAT_STRING = u'{body}'

  SOURCE_LONG = u'Test Text Parser'


class TestTextParser(text_parser.SlowLexicalTextParser):
  """Implement a text parser object that can successfully parse a text file.

  To be able to achieve that one function has to be implemented, the ParseDate
  one.
  """
  NAME = u'test_text'

  tokens = [
      lexer.Token(u'INITIAL', r'^([\d\/]+) ', u'SetDate', u'TIME'),
      lexer.Token(u'TIME', r'([0-9:\.]+) ', u'SetTime', u'STRING_HOST'),
      lexer.Token(u'STRING_HOST', r'([^\-]+)- ', u'ParseStringHost', u'STRING'),
      lexer.Token(u'STRING', r'([^\n]+)', u'ParseString', u''),
      lexer.Token(u'STRING', r'\n', u'ParseMessage', u'INITIAL')]

  def ParseStringHost(self, match, **_):
    user, host = match.group(1).split(u':')
    self.attributes[u'hostname'] = host
    self.attributes[u'username'] = user

  def SetDate(self, match, **_):
    month, day, year = match.group(1).split(u'/')
    self.attributes[u'imonth'] = int(month)
    self.attributes[u'iyear'] = int(year)
    self.attributes[u'iday'] = int(day)

  def Scan(self, unused_file_entry):
    pass

  def CreateEvent(self, timestamp, offset, attributes):
    event_object = TestTextEvent(timestamp, 0, attributes)
    event_object.offset = offset
    return event_object


class TextParserTest(test_lib.ParserTestCase):
  """An unit test for the plaso parser library."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._parser = TestTextParser()

  def testTextParserFail(self):
    """Test a text parser that will not match against content."""
    test_file = self._GetTestFilePath([u'text_parser', u'test1.txt'])

    with self.assertRaises(errors.UnableToParseFile):
      _ = self._ParseFile(self._parser, test_file)

  def testTextParserSuccess(self):
    """Test a text parser that will match against content."""
    formatters_manager.FormattersManager.RegisterFormatter(
        TestTextEventFormatter)

    formatter_mediator = formatters_mediator.FormatterMediator()

    test_file = self._GetTestFilePath([u'text_parser', u'test2.txt'])
    event_queue_consumer = self._ParseFile(self._parser, test_file)
    event_objects = self._GetEventObjectsFromQueue(event_queue_consumer)

    event_object = event_objects[0]

    msg1, _ = formatters_manager.FormattersManager.GetMessageStrings(
        formatter_mediator, event_object)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2011-01-01 05:23:15')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(msg1, u'first line.')
    self.assertEqual(event_object.hostname, u'myhost')
    self.assertEqual(event_object.username, u'myuser')

    event_object = event_objects[1]

    msg2, _ = formatters_manager.FormattersManager.GetMessageStrings(
        formatter_mediator, event_object)

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'1991-12-24 19:58:06')
    self.assertEqual(event_object.timestamp, expected_timestamp)

    self.assertEqual(msg2, u'second line.')
    self.assertEqual(event_object.hostname, u'myhost')
    self.assertEqual(event_object.username, u'myuser')

    formatters_manager.FormattersManager.DeregisterFormatter(
        TestTextEventFormatter)


class PyParserTest(test_lib.ParserTestCase):
  """Few unit tests for the pyparsing unit."""

  def _CheckIPv4(self, ip_address):
    # TODO: Add a similar IPv6 check.
    try:
      text_parser.PyparsingConstants.IPV4_ADDRESS.parseString(ip_address)
      return True
    except pyparsing.ParseException:
      return False

  def testPyConstantIPv4(self):
    """Run few tests to make sure the constants are working."""
    self.assertTrue(self._CheckIPv4(u'123.51.234.52'))
    self.assertTrue(self._CheckIPv4(u'255.254.23.1'))
    self.assertTrue(self._CheckIPv4(u'1.1.34.2'))
    self.assertFalse(self._CheckIPv4(u'1.1.34.258'))
    self.assertFalse(self._CheckIPv4(u'a.1.34.258'))
    self.assertFalse(self._CheckIPv4(u'.34.258'))
    self.assertFalse(self._CheckIPv4(u'34.258'))
    self.assertFalse(self._CheckIPv4(u'10.52.34.258'))

  def testPyConstantOctet(self):
    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.IPV4_OCTET.parseString(u'526')

    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.IPV4_OCTET.parseString(u'1026')

    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.IPV4_OCTET.parseString(
          u'a9', parseAll=True)

  def testPyConstantOthers(self):
    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.MONTH.parseString(u'MMo')
    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.MONTH.parseString(u'M')
    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.MONTH.parseString(u'March', parseAll=True)

    self.assertTrue(text_parser.PyparsingConstants.MONTH.parseString(u'Jan'))

    line = u'# This is a comment.'
    parsed_line = text_parser.PyparsingConstants.COMMENT_LINE_HASH.parseString(
        line)
    self.assertEqual(parsed_line[-1], u'This is a comment.')
    self.assertEqual(len(parsed_line), 2)


if __name__ == u'__main__':
  unittest.main()
