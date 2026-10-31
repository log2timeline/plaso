#!/usr/bin/env python3
"""Tests for PL-SQL recall file parser."""

import unittest

from plaso.lib import errors
from plaso.parsers import pls_recall

from tests.parsers import test_lib


class PlsRecallTest(test_lib.ParserTestCase):
    """Tests for PL-SQL recall file parser."""

    def testParse(self):
        """Tests the Parse function."""
        parser = pls_recall.PlsRecallParser()
        storage_writer = self._ParseFile(["PLSRecall_Test.dat"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 2)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # typos:disable
        # Note that the test file actually has 'test_databae' in the table name.
        expected_event_values = {
            "data_type": "pls_recall:entry",
            "database_name": "DB11",
            "query": "SELECT * from test_databae where date > '01/01/2012'",
            "sequence_number": 206,
            "username": "tsltmp",
            "written_time": "2013-06-18T19:50:00.550000+00:00",
        }
        # typos:enable

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testParseFileObjectWithText(self):
        """Tests the ParseFileObject function on text that is not PLS Recall."""
        # Text where bytes 4 to 12 form a plausible TDateTime value and the Text
        # field, at offset 124, starts with a PL/SQL keyword, but where the
        # Username and Database fields do not contain an end-of-string character.
        data = b".TH 1.4 @@@@ \n.SH DESCRIPTION\n"
        data += b"x" * (123 - len(data)) + b"\n"
        data += b"set the access control options for the network services.\n" * 80

        parser = pls_recall.PlsRecallParser()
        storage_writer = self._CreateStorageWriter()
        parser_mediator = self._CreateParserMediator(storage_writer)
        file_object = self._CreateFileObject("tcpd.8", data)

        with self.assertRaises(errors.WrongParser):
            parser.ParseFileObject(parser_mediator, file_object)


if __name__ == "__main__":
    unittest.main()
