#!/usr/bin/env python3
"""Tests for the Windows EventLog providers helper."""

import unittest

from plaso.containers import artifacts
from plaso.helpers.windows import eventlog_providers

from tests import test_lib as shared_test_lib


class WindowsEventLogProvidersHelperTest(shared_test_lib.BaseTestCase):
    """Tests for the Windows EventLog providers helper."""

    # pylint: disable=protected-access

    def testGetNormalizedPath(self):
        """Tests the _GetNormalizedPath function."""
        test_helper = eventlog_providers.WindowsEventLogProvidersHelper()

        normalized_path = test_helper._GetNormalizedPath(
            "%SystemRoot%\\System32\\IoLogMsg.dll"
        )
        self.assertEqual(normalized_path, "%SystemRoot%\\System32\\IoLogMsg.dll")

        normalized_path = test_helper._GetNormalizedPath(
            "%windir%\\System32\\lsasrv.dll"
        )
        self.assertEqual(normalized_path, "%SystemRoot%\\System32\\lsasrv.dll")

        normalized_path = test_helper._GetNormalizedPath(
            "C:\\Windows\\System32\\mscoree.dll"
        )
        self.assertEqual(normalized_path, "%SystemRoot%\\System32\\mscoree.dll")

        normalized_path = test_helper._GetNormalizedPath("werfault.exe")
        self.assertEqual(normalized_path, "%SystemRoot%\\System32\\werfault.exe")

        normalized_path = test_helper._GetNormalizedPath(
            "system32\\drivers\\WdFilter.sys"
        )
        self.assertEqual(
            normalized_path, "%SystemRoot%\\System32\\drivers\\WdFilter.sys"
        )
        normalized_path = test_helper._GetNormalizedPath(
            "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\84.0.522.52\\"
            "eventlog_provider.dll"
        )
        expected_normalized_path = (
            "\\Program Files (x86)\\Microsoft\\Edge\\Application\\84.0.522.52\\"
            "eventlog_provider.dll"
        )
        self.assertEqual(normalized_path, expected_normalized_path)

        normalized_path = test_helper._GetNormalizedPath(
            "%ProgramFiles%\\Windows Defender\\MpClient.dll"
        )
        self.assertEqual(
            normalized_path, "%ProgramFiles%\\Windows Defender\\MpClient.dll"
        )
        normalized_path = test_helper._GetNormalizedPath(
            "%programdata%\\Microsoft\\Windows Defender\\Definition Updates\\"
            "Default\\MpEngine.dll"
        )
        expected_normalized_path = (
            "%programdata%\\Microsoft\\Windows Defender\\Definition Updates\\"
            "Default\\MpEngine.dll"
        )
        self.assertEqual(normalized_path, expected_normalized_path)

        normalized_path = test_helper._GetNormalizedPath(
            "$(runtime.system32)\\WinML.dll"
        )
        self.assertEqual(normalized_path, "%SystemRoot%\\System32\\WinML.dll")

        normalized_path = test_helper._GetNormalizedPath(
            "$(runtime.windows)\\immersivecontrolpanel\\systemsettings.exe"
        )
        self.assertEqual(
            normalized_path, "%SystemRoot%\\immersivecontrolpanel\\systemsettings.exe"
        )
        normalized_path = test_helper._GetNormalizedPath("\\eventlogmessages.dll")
        self.assertEqual(normalized_path, "\\eventlogmessages.dll")

    def testMerge(self):
        """Tests the Merge function."""
        test_helper = eventlog_providers.WindowsEventLogProvidersHelper()

        first_event_log_provider = artifacts.WindowsEventLogProviderArtifact(
            event_message_files=["%SystemRoot%\\System32\\IoLogMsg.dll"],
            log_source="disk",
            log_type="system",
        )
        second_event_log_provider = artifacts.WindowsEventLogProviderArtifact(
            category_message_files=["C:\\Windows\\System32\\catmsg.dll"],
            event_message_files=[
                "%windir%\\System32\\IoLogMsg.dll",
                "werfault.exe",
            ],
            identifier="{6b510852-3583-4e2d-affe-a67f9f223438}",
            log_source="Disk",
            log_type="Application",
            parameter_message_files=["system32\\kernel32.dll"],
        )

        test_helper.Merge(first_event_log_provider, second_event_log_provider)

        self.assertEqual(
            first_event_log_provider.identifier,
            "{6b510852-3583-4e2d-affe-a67f9f223438}",
        )
        self.assertIsNone(first_event_log_provider.additional_identifier)
        self.assertEqual(first_event_log_provider.log_sources, ["disk"])
        self.assertEqual(first_event_log_provider.log_types, ["system", "application"])
        self.assertEqual(
            first_event_log_provider.category_message_files,
            ["%SystemRoot%\\System32\\catmsg.dll"],
        )
        self.assertEqual(
            first_event_log_provider.event_message_files,
            [
                "%SystemRoot%\\System32\\IoLogMsg.dll",
                "%SystemRoot%\\System32\\werfault.exe",
            ],
        )
        self.assertEqual(
            first_event_log_provider.parameter_message_files,
            ["%SystemRoot%\\System32\\kernel32.dll"],
        )

        # A provider with a different identifier is stored as the additional
        # identifier.
        third_event_log_provider = artifacts.WindowsEventLogProviderArtifact(
            identifier="{a0e3d8ea-c34f-4419-a1db-90435b8b21d0}"
        )

        test_helper.Merge(first_event_log_provider, third_event_log_provider)

        self.assertEqual(
            first_event_log_provider.identifier,
            "{6b510852-3583-4e2d-affe-a67f9f223438}",
        )
        self.assertEqual(
            first_event_log_provider.additional_identifier,
            "{a0e3d8ea-c34f-4419-a1db-90435b8b21d0}",
        )

    def testNormalizeMessageFiles(self):
        """Tests the NormalizeMessageFiles function."""
        test_helper = eventlog_providers.WindowsEventLogProvidersHelper()

        event_log_provider = artifacts.WindowsEventLogProviderArtifact(
            category_message_files=["%windir%\\System32\\lsasrv.dll"],
            event_message_files=[
                "C:\\Windows\\System32\\mscoree.dll",
                "werfault.exe",
            ],
            parameter_message_files=["$(runtime.system32)\\WinML.dll"],
        )

        test_helper.NormalizeMessageFiles(event_log_provider)

        self.assertEqual(
            event_log_provider.category_message_files,
            ["%SystemRoot%\\System32\\lsasrv.dll"],
        )
        self.assertEqual(
            event_log_provider.event_message_files,
            [
                "%SystemRoot%\\System32\\mscoree.dll",
                "%SystemRoot%\\System32\\werfault.exe",
            ],
        )
        self.assertEqual(
            event_log_provider.parameter_message_files,
            ["%SystemRoot%\\System32\\WinML.dll"],
        )


if __name__ == "__main__":
    unittest.main()
