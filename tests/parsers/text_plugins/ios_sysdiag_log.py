#!/usr/bin/env python3
"""Tests for the iOS Mobile Installation log text parser plugin."""

import io
import unittest

from plaso.parsers import mediator as parsers_mediator
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import ios_sysdiag_log

from tests.parsers.text_plugins import test_lib


class IOSSysdiagLogTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the iOS Mobile Installation log text parser plugin."""

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        plugin = ios_sysdiag_log.IOSSysdiagLogTextPlugin()
        parser_mediator = parsers_mediator.ParserMediator()

        file_object = io.BytesIO(
            b"Wed Aug 11 05:51:02 2021 [176] <notice> (0x16bae7000) "
            b"-[MIContainer makeContainerLiveReplacingContainer:reason:"
            b"waitForDeletion:withError:] : Made container live for "
            b"com.apple.CoreCDPUI.localSecretPrompt at /private/var/mobile/"
            b"Containers/Data/PluginKitPlugin/B327BDD9-BD0D-490A-9A31-"
            b"D07E95DB23E1\n"
        )
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        self.assertTrue(plugin.CheckRequiredFormat(parser_mediator, text_reader))

        # Check non-matching format.
        file_object = io.BytesIO(
            b"Jan 22 07:52:33 myhostname.myhost.com client[30840]: INFO No new "
            b"content in image.dd.\n"
        )
        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        self.assertFalse(plugin.CheckRequiredFormat(parser_mediator, text_reader))

    def testProcess(self):
        """Tests the Process function."""
        plugin = ios_sysdiag_log.IOSSysdiagLogTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["ios_sysdiag.log"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 28)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        expected_event_values = {
            "body": (
                "Ignoring plugin at /System/Library/PrivateFrameworks/"
                "AccessibilityUtilities.framework/PlugIns/com.apple.accessibility."
                "Accessibility.HearingAidsTapToRadar.appex due to validation "
                "issue(s). See previous log messages for details."
            ),
            "originating_call": (
                "+[MILaunchServicesDatabaseGatherer "
                "enumeratePluginKitPluginsInBundle:updatingPluginParentID:"
                "ensurePluginsAreExecutable:installProfiles:error:enumerator:]"
            ),
            "process_identifier": 176,
            "severity": "err",
            "written_time": "2021-08-11T05:51:02+00:00",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 7)
        self.CheckEventData(event_data, expected_event_values)


if __name__ == "__main__":
    unittest.main()
