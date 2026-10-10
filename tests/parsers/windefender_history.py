#!/usr/bin/env python3
"""Tests for the Windows Defender History parser."""

import unittest

from plaso.parsers import windefender_history

from tests.parsers import test_lib


class WinDefenderHistoryUnitTest(test_lib.ParserTestCase):
    """Tests for the Windows Defender History parser."""

    def testWebFileDetection(self):
        """Tests parsing a webfile Detection History file."""
        parser = windefender_history.WinDefenderHistoryParser()
        storage_writer = self._ParseFile(
            ["windefender_history", "FC380697-A68D-4C94-B67F-9B6449039463"], parser
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "category": 27,
            "data_type": "av:defender:detection_history",
            "filename": "C:\\Users\\testuser\\Downloads\\PotentiallyUnwanted.exe",
            "host_and_user": "FRYPTOP\\testuser",
            "initial_detection_time": "2022-07-22T05:32:27.6558959+00:00",
            "last_threat_status_change_time": "2022-07-22T05:32:28.5123912+00:00",
            "process": "C:\\Windows\\explorer.exe",
            "recorded_time": "2022-07-22T05:32:27.8302783+00:00",
            "remediation_account": None,
            "remediation_time": None,
            "severity": 1,
            "sha256": (
                "d6f6c6b9fde37694e12b12009ad11ab9ec8dd0f193e7319c523933bdad8a50ad"
            ),
            "threat_identifier": 224688,
            "threat_name": "PUA:Win32/EICAR_Test_File",
            "threat_status": 1,
            "web_filenames": [
                (
                    "C:\\Users\\testuser\\Downloads\\PotentiallyUnwanted.exe|"
                    "http://amtso.eicar.org/PotentiallyUnwanted.exe|"
                    "pid:19588,ProcessStart:133029415464710822"
                )
            ],
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testContainerDetection(self):
        """Tests parsing a containerfile Detection History file."""
        parser = windefender_history.WinDefenderHistoryParser()
        storage_writer = self._ParseFile(
            ["windefender_history", "6AFE33A0-19BA-4FFF-892F-B700539D7D63"], parser
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "category": 42,
            "container_filenames": ["C:\\Users\\testuser\\Downloads\\eicar_com.zip"],
            "data_type": "av:defender:detection_history",
            "filename": "C:\\Users\\testuser\\Downloads\\eicar_com.zip->eicar.com",
            "host_and_user": "FRYPTOP\\testuser",
            "initial_detection_time": "2022-07-22T05:36:18.9293722+00:00",
            "last_threat_status_change_time": "2022-07-22T05:37:02.7574371+00:00",
            "process": "Unknown",
            "recorded_time": "2022-07-22T05:36:18.9094421+00:00",
            "remediation_account": "NT AUTHORITY\\SYSTEM",
            "remediation_time": "2022-07-22T05:37:02.7574371+00:00",
            "severity": 5,
            "sha256": (
                "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f"
            ),
            "threat_identifier": 2147519003,
            "threat_name": "Virus:DOS/EICAR_Test_File",
            "threat_status": 103,
            "web_filenames": [
                (
                    "C:\\Users\\testuser\\Downloads\\eicar_com.zip|"
                    "https://secure.eicar.org/eicar_com.zip|"
                    "pid:20580,ProcessStart:133029417782902463"
                )
            ],
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testQuarantinedFileDetection(self):
        """Tests parsing a Detection History file of a quarantined file."""
        parser = windefender_history.WinDefenderHistoryParser()
        storage_writer = self._ParseFile(
            ["windefender_history", "7C66C39C-49DD-42D7-9822-4039C98CC246"], parser
        )

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "category": 42,
            "container_filenames": [],
            "data_type": "av:defender:detection_history",
            "filename": "C:\\wmilab\\eicar\\eicar1.com",
            "host_and_user": "plaso\\batman",
            "initial_detection_time": "2026-10-10T16:52:13.2022359+00:00",
            "last_threat_status_change_time": "2026-10-10T16:54:08.6242655+00:00",
            "process": "C:\\Windows\\System32\\WindowsPowerShell\\v1.0\\powershell.exe",
            "recorded_time": "2026-10-10T16:52:13.1718776+00:00",
            "remediation_account": "NT AUTHORITY\\SYSTEM",
            "remediation_time": "2026-10-10T16:54:08.6242655+00:00",
            "severity": 5,
            "sha256": (
                "275a021bbfb6489e54d471899f7db9d1663fc695ec2fe2a2c4538aabf651fd0f"
            ),
            "threat_identifier": 2147519003,
            "threat_name": "Virus:DOS/EICAR_Test_File",
            "threat_status": 3,
            "web_filenames": [],
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
