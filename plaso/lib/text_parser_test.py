#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains the tests for the generic text parser."""

import unittest

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import lexer
from plaso.lib import parser
from plaso.lib import text_parser

import pyparsing
import pytz


class EmtpyObject(object):
  """An empty object."""


class FakeFile(object):
  """Implements a fake file object, with content."""

  LINES = ('first line.', 'second line.', 'third line.')

  def __init__(self):
    self.buffer = ''
    self.name = 'IamFakeFile'
    self.display_name = self.name
    self.index = 0
    self.offset = 0
    self.size = 0
    for line in self.LINES:
      self.size += len(line)

  # We are implementing an interface.
  def readline(self):
    """Provides a "fake" readline function."""
    ret = ''
    if self.index < len(self.LINES):
      ret = self.LINES[self.index]

    self.index += 1
    self.offset += len(ret)
    return ret

  # We are implementing an interface.
  def read(self, read_size):
    if len(self.buffer) > read_size:
      ret = self.buffer[:read_size]
      self.buffer = self.buffer[read_size:]
      self.offset += len(ret)
      return ret

    if self.index < len(self.LINES):
      # Add to buffer.
      self.buffer += self.LINES[self.index]
      self.index += 1
      return self.read(read_size)

    ret = self.buffer
    self.buffer = ''
    self.offset += len(ret)
    return ret

  # We are implementing an interface.
  def seek(self, offset, whence=0):
    if whence == 0:
      self.index = 0
      self.buffer = ''
      self.offset = 0
      _ = self.read(offset)
    elif whence == 1:
      if offset > 0:
        _ = self.read(offset)
      else:
        ofs = self.offset + offset
        self.seek(ofs)
    elif whence == 2:
      ofs = self.size + offset
      if ofs > self.offset:
        _ = self.read(ofs - self.offset)
      else:
        self.seek(0)
        _ = self.read(ofs)
    else:
      raise RuntimeError('Illegal whence value %s' % whence)

  # We are implementing an interface.
  def tell(self):
    return self.offset

  def __iter__(self):
    while 1:
      line = self.readline()
      if not line:
        break
      yield line


class FakeBetterFile(FakeFile):
  """Implements a fake file object, with content."""

  LINES = ('01/01/2011 05:23:15 myuser:myhost- first line.\n',
           '12/24/1991 19:58:06 myuser:myhost- second line.\n',
           '06/01/1945 08:20:00 myuser:myhost- third line.\n')


class TestTextEvent(event.TextEvent):
  """Test text event."""
  DATA_TYPE = 'test:parser:text'


class TestTextEventFormatter(eventdata.EventFormatter):
  """Test text event formatter."""
  DATA_TYPE = 'test:parser:text'
  FORMAT_STRING = u'{body}'

  SOURCE_LONG = 'Test Text Parser'


class TestTextParser(text_parser.SlowLexicalTextParser):
  """Implement a text parser object that can successfully parse a text file.

  To be able to achieve that one function has to be implemented, the ParseDate
  one.
  """
  tokens = [
      lexer.Token('INITIAL',
                  r'^([\d\/]+) ', 'SetDate', 'TIME'),
      lexer.Token('TIME', r'([0-9:\.]+) ', 'SetTime', 'STRING_HOST'),
      lexer.Token('STRING_HOST', r'([^\-]+)- ', 'ParseStringHost', 'STRING'),
      lexer.Token('STRING', '([^\n]+)', 'ParseString', ''),
      lexer.Token('STRING', '\n', 'ParseMessage', 'INITIAL'),
      ]

  def ParseStringHost(self, match, **_):
    user, host = match.group(1).split(':')
    self.attributes['hostname'] = host
    self.attributes['username'] = user

  def SetDate(self, match, **_):
    month, day, year = match.group(1).split('/')
    self.attributes['imonth'] = int(month)
    self.attributes['iyear'] = int(year)
    self.attributes['iday'] = int(day)

  def Scan(self, filehandle):
    pass

  def CreateEvent(self, timestamp, offset, attributes):
    event_object = TestTextEvent(timestamp, attributes)
    event_object.offset = offset
    return event_object


class PlasoParserTest(unittest.TestCase):
  """An unit test for the plaso parser library."""

  def testParserNotImplemented(self):
    """Test the base class Parse function."""
    self.assertRaises(TypeError, parser.PlasoParser)


class TextParserTest(unittest.TestCase):
  """An unit test for the plaso parser library."""

  def setUp(self):
    self._pre_obj = EmtpyObject()
    self._pre_obj.zone = pytz.UTC

  def testTextParserFail(self):
    """Test a text parser that will not match against content."""
    my_text_parser = TestTextParser(self._pre_obj, None)
    fn = FakeFile()

    text_generator = my_text_parser.Parse(fn)
    self.assertRaises(errors.UnableToParseFile, list, text_generator)

  def testTextParserSuccess(self):
    """Test a text parser that will match against content."""
    my_text_parser = TestTextParser(self._pre_obj, None)
    fn = FakeBetterFile()

    text_generator = my_text_parser.Parse(fn)

    first_entry = text_generator.next()
    second_entry = text_generator.next()

    msg1, _ = eventdata.EventFormatterManager.GetMessageStrings(first_entry)
    self.assertEquals(first_entry.timestamp, 1293859395000000)
    self.assertEquals(msg1, 'first line.')
    self.assertEquals(first_entry.hostname, 'myhost')
    self.assertEquals(first_entry.username, 'myuser')

    msg2, _ = eventdata.EventFormatterManager.GetMessageStrings(second_entry)
    self.assertEquals(second_entry.timestamp, 693604686000000)
    self.assertEquals(msg2, 'second line.')
    self.assertEquals(second_entry.hostname, 'myhost')
    self.assertEquals(second_entry.username, 'myuser')


class PyParserTest(unittest.TestCase):
  """Few unit tests for the pyparsing unit."""

  def testPyConstantIPv4(self):
    """Run few tests to make sure the constants are working."""
    self.assertTrue(self._CheckIPv4('123.51.234.52'))
    self.assertTrue(self._CheckIPv4('255.254.23.1'))
    self.assertTrue(self._CheckIPv4('1.1.34.2'))
    self.assertFalse(self._CheckIPv4('1.1.34.258'))
    self.assertFalse(self._CheckIPv4('a.1.34.258'))
    self.assertFalse(self._CheckIPv4('.34.258'))
    self.assertFalse(self._CheckIPv4('34.258'))
    self.assertFalse(self._CheckIPv4('10.52.34.258'))

  def testPyConstantOctet(self):
    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.IPV4_OCTET.parseString('526')

    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.IPV4_OCTET.parseString('1026')

    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.IPV4_OCTET.parseString(
          'a9', parseAll=True)

  def testPyConstantOthers(self):
    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.MONTH.parseString('MMo')
    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.MONTH.parseString('M')
    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.MONTH.parseString('March', parseAll=True)

    self.assertTrue(text_parser.PyparsingConstants.MONTH.parseString('Jan'))

    line = '# This is a comment.'
    parsed_line = text_parser.PyparsingConstants.COMMENT_LINE_HASH.parseString(
        line)
    self.assertEquals(parsed_line[-1], 'This is a comment.')
    self.assertEquals(len(parsed_line), 2)

  def _CheckIPv4(self, ip_address):
    # TODO: Add a similar IPv6 check.
    try:
      text_parser.PyparsingConstants.IPV4_ADDRESS.parseString(ip_address)
      return True
    except pyparsing.ParseException:
      return False


if __name__ == '__main__':
  unittest.main()
