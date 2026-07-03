#!/usr/bin/env python3
"""Tests for the Symantec AV Log parser."""

import unittest

from plaso.parsers import symantec

from tests.parsers import test_lib


class SymantecAccessProtectionUnitTest(test_lib.ParserTestCase):
    """Tests for the Symantec AV Log parser."""

    # pylint: disable=protected-access

    def testParse(self):
        """Tests the Parse function."""
        parser = symantec.SymantecParser()
        storage_writer = self._ParseFile(["Symantec.Log"], parser)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 8)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "access": "1",
            "action0": "14",
            "action1": "5",
            "action1_status": None,
            "action2": "3",
            "action2_status": None,
            "address": None,
            "backup_identifier": "0",
            "category": "1",
            "cleaninfo": "2",
            "client_group": None,
            "compressed": "0",
            "data_type": "av:symantec:scanlog",
            "definfo": None,
            "def_sequence_number": "0",
            "deleteinfo": "4",
            "depth": "0",
            "description": None,
            "domain_identifier": None,
            "domain_name": None,
            "error_code": None,
            "event_code": "5",
            "event_fields": [
                "201",
                "4",
                "6",
                "1",
                "65542",
                "0",
                "0",
                "0",
                "0",
                "0",
                "0",
            ],
            "extra": None,
            "file_path": "D:\\Twinkle_Prod$\\VM11 XXX\\outside\\test.exe.txt",
            "flags": "39866436",
            "group_identifier": "0",
            "hostname": "SQLZZSERVEDD",
            "identifier": "{AAAAAAA-4F7F-4896-8C5A-5CEDFB6A9DC0}",
            "last_written_time": "2012-11-30T10:47:29",
            "license_expiration_date": None,
            "license_feature_name": None,
            "license_feature_version": None,
            "license_fulfillment_identifier": None,
            "license_lifecycle": None,
            "license_seats_delta": None,
            "license_seats": None,
            "license_seats_total": None,
            "license_serial_number": None,
            "license_start_date": None,
            "logger": "2",
            "login_domain": None,
            "log_session_identifier": "74ac79f8-d0c0-4065-acd7-27af2fc7ec4c",
            "mac_address": "00:30:12:9C:58:3B",
            "new_ext": None,
            "ntdomain": "BUSINES1",
            "offset": 233,
            "parent": None,
            "quarfwd_status": "0",
            "remote_ip_address": None,
            "remote_machine": None,
            "scan_identifier": "0",
            "username": "davnads",
            "virus": "W32.Changeup!gen33",
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 1)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
