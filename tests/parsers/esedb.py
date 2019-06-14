#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the Extensible Storage Engine (ESE) database files (EDB) parser."""

from __future__ import unicode_literals

import unittest

from plaso.parsers import esedb
from plaso.parsers import esedb_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


class ESEDBParserTest(test_lib.ParserTestCase):
  """Tests for the Extensible Storage Engine database (ESEDB) file parser."""

  def testParse(self):
    """Tests the Parse function."""
    parser = esedb.ESEDBParser()
    storage_writer = self._ParseFile(['Windows.edb'], parser)

    # Extensible Storage Engine Database information:
    #     File type:              Database
    #     Created in format:      0x620,17
    #     Current format:         0x620,17
    #     Page size:              32768 bytes

    self.assertEqual(storage_writer.number_of_warnings, 0)
    self.assertEqual(storage_writer.number_of_events, 0)

    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)
    parser = esedb.ESEDBParser()
    parser.ParseFileObject(parser_mediator, None)

    self.assertEqual(storage_writer.number_of_warnings, 1)
    self.assertEqual(storage_writer.number_of_events, 0)

    warnings = list(storage_writer.GetWarnings())

    warning = warnings[0]
    self.assertIsNotNone(warning)

    self.assertTrue(warning.message.startswith(
        'unable to open file with error: pyesedb_file_open_file_object: '))


if __name__ == '__main__':
  unittest.main()
