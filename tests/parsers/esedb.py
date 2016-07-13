#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the Extensible Storage Engine (ESE) database files (EDB) parser."""

import unittest

from plaso.parsers import esedb
from plaso.parsers import esedb_plugins  # pylint: disable=unused-import

from tests.parsers import test_lib


class ESEDBParserTest(test_lib.ParserTestCase):
  """Tests for the Extensible Storage Engine database (ESEDB) file parser."""

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

    expected_message = (
        u'unable to open file with error: '
        u'pyesedb_file_open_file_object: unable to open file. '
        u'pyesedb_file_object_get_offset: unable to retrieve current offset '
        u'in file object with error: "\'NoneType\' object has no attribute '
        u'\'tell\'". '
        u'pyesedb_file_object_io_handle_get_size: unable to retrieve current '
        u'offset in file object. '
        u'pyesedb_file_object_seek_offset: unable to seek in file object with '
        u'error: "\'NoneType\' object has no attribute \'seek\'". '
        u'pyesedb_file_object_io_handle_seek_offset: unable to seek in file '
        u'object. '
        u'libbfio_handle_seek_offset: unable to find offset: -1 in handle. '
        u'libesedb_io_handle_read_file_header: unable to seek file header '
        u'offset: 0. '
        u'libesedb_file_open_read: unable to read (database) file header. '
        u'libesedb_file_open_file_io_handle: unable to read from file handle.')
    self.assertEqual(error.message, expected_message)


if __name__ == '__main__':
  unittest.main()
