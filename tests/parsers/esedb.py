#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Extensible Storage Engine (ESE) database files (EDB) parser."""

import unittest

from plaso.parsers import esedb
from plaso.parsers import esedb_plugins  # pylint: disable=unused-import

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class ESEDBParserTest(test_lib.ParserTestCase):
  """Tests for the Extensible Storage Engine database (ESEDB) file parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'Windows.edb'])
  def testParse(self):
    """Tests the Parse function."""
    parser_object = esedb.ESEDBParser()
    storage_writer = self._ParseFile([u'Windows.edb'], parser_object)

    # Extensible Storage Engine Database information:
    #     File type:              Database
    #     Created in format:      0x620,17
    #     Current format:         0x620,17
    #     Page size:              32768 bytes

    self.assertEqual(len(storage_writer.events), 0)
    self.assertEqual(len(storage_writer.errors), 0)

    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)
    parser_object = esedb.ESEDBParser()
    parser_object.ParseFileObject(parser_mediator, None)

    self.assertEqual(len(storage_writer.events), 0)
    self.assertEqual(len(storage_writer.errors), 1)

    error = storage_writer.errors[0]
    self.assertIsNotNone(error)

    self.assertTrue(error.message.startswith(
        u'unable to open file with error: pyesedb_file_open_file_object: '))


if __name__ == '__main__':
  unittest.main()
