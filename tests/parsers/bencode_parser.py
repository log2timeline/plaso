#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for Bencode file parser."""

import unittest

from plaso.parsers import bencode_parser

from tests.parsers import test_lib


class BencodeTest(test_lib.ParserTestCase):
  """Tests for Bencode file parser."""

  def setUp(self):
    """Makes preparations before running an individual test."""
    self._parser = bencode_parser.BencodeParser()

  # TODO: add tests.


if __name__ == '__main__':
  unittest.main()
