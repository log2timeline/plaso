#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""This file contains the tests for the generic text parser."""

from __future__ import unicode_literals

import unittest

import pyparsing

from plaso.parsers import text_parser

from tests.parsers import test_lib


class PyparsingConstantsTest(test_lib.ParserTestCase):
  """Tests the PyparsingConstants text parser."""

  def testConstants(self):
    """Tests parsing with constants."""
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
    self.assertEqual(parsed_line[-1], 'This is a comment.')
    self.assertEqual(len(parsed_line), 2)

  def testConstantIPv4(self):
    """Tests parsing with the IPV4_ADDRESS constant."""
    self.assertTrue(
        text_parser.PyparsingConstants.IPV4_ADDRESS.parseString(
            '123.51.234.52'))
    self.assertTrue(
        text_parser.PyparsingConstants.IPV4_ADDRESS.parseString(
            '255.254.23.1'))
    self.assertTrue(
        text_parser.PyparsingConstants.IPV4_ADDRESS.parseString('1.1.34.2'))

    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.IPV4_ADDRESS.parseString('1.1.34.258')

    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.IPV4_ADDRESS.parseString('a.1.34.258')

    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.IPV4_ADDRESS.parseString('.34.258')

    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.IPV4_ADDRESS.parseString('34.258')

    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.IPV4_ADDRESS.parseString('10.52.34.258')

  def testConstantOctet(self):
    """Tests parsing with the IPV4_OCTET constant."""
    self.assertTrue(
        text_parser.PyparsingConstants.IPV4_OCTET.parseString('0'))

    self.assertTrue(
        text_parser.PyparsingConstants.IPV4_OCTET.parseString('123'))

    self.assertTrue(
        text_parser.PyparsingConstants.IPV4_OCTET.parseString('255'))

    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.IPV4_OCTET.parseString('526')

    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.IPV4_OCTET.parseString('1026')

    with self.assertRaises(pyparsing.ParseException):
      text_parser.PyparsingConstants.IPV4_OCTET.parseString(
          'a9', parseAll=True)


if __name__ == '__main__':
  unittest.main()
