#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the OLE Compound Files (OLECF) parser."""

import unittest

from plaso.lib import definitions
from plaso.lib import timelib
from plaso.parsers import olecf
from plaso.parsers import olecf_plugins  # pylint: disable=unused-import

from tests import test_lib as shared_test_lib
from tests.parsers import test_lib


class OLECFParserTest(test_lib.ParserTestCase):
  """Tests for the OLE Compound Files (OLECF) parser."""

  @shared_test_lib.skipUnlessHasTestFile([u'Document.doc'])
  def testParse(self):
    """Tests the Parse function."""
    parser = olecf.OLECFParser()
    storage_writer = self._ParseFile([u'Document.doc'], parser)

    # OLE Compound File information:
    #     Version             : 3.62
    #     Sector size         : 512
    #     Short sector size   : 64

    self.assertEqual(storage_writer.number_of_events, 9)
    self.assertEqual(storage_writer.number_of_errors, 0)

    events = list(storage_writer.GetEvents())

    event = events[8]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-05-16 02:29:49.785')
    self.assertEqual(event.timestamp, expected_timestamp)
    self.assertEqual(
        event.timestamp_desc,
        definitions.TIME_DESCRIPTION_MODIFICATION)

    self.assertEqual(event.data_type, u'olecf:item')
    self.assertEqual(event.offset, 0)

    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)
    parser = olecf.OLECFParser()
    parser.ParseFileObject(parser_mediator, None)

    self.assertEqual(storage_writer.number_of_events, 0)
    self.assertEqual(storage_writer.number_of_errors, 1)

    errors = list(storage_writer.GetErrors())

    error = errors[0]
    self.assertIsNotNone(error)

    self.assertTrue(error.message.startswith(
        u'unable to open file with error: pyolecf_file_open_file_object: '))


if __name__ == '__main__':
  unittest.main()
