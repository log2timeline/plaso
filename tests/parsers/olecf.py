#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the OLE Compound Files (OLECF) parser."""

import unittest

from plaso.lib import eventdata
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
    parser_object = olecf.OLECFParser()
    storage_writer = self._ParseFile([u'Document.doc'], parser_object)

    # OLE Compound File information:
    #     Version             : 3.62
    #     Sector size         : 512
    #     Short sector size   : 64

    self.assertEqual(len(storage_writer.events), 9)
    self.assertEqual(len(storage_writer.errors), 0)

    event_object = storage_writer.events[8]

    expected_timestamp = timelib.Timestamp.CopyFromString(
        u'2013-05-16 02:29:49.785')
    self.assertEqual(event_object.timestamp, expected_timestamp)
    self.assertEqual(
        event_object.timestamp_desc,
        eventdata.EventTimestamp.MODIFICATION_TIME)

    self.assertEqual(event_object.data_type, u'olecf:item')
    self.assertEqual(event_object.offset, 0)

    storage_writer = self._CreateStorageWriter()
    parser_mediator = self._CreateParserMediator(storage_writer)
    parser_object = olecf.OLECFParser()
    parser_object.ParseFileObject(parser_mediator, None)

    self.assertEqual(len(storage_writer.events), 0)
    self.assertEqual(len(storage_writer.errors), 1)

    error = storage_writer.errors[0]
    self.assertIsNotNone(error)

    self.assertTrue(error.message.startswith(
        u'unable to open file with error: pyolecf_file_open_file_object: '))


if __name__ == '__main__':
  unittest.main()
