#!/usr/bin/env python3
"""Tests for the SCCM log text parser plugin."""

import threading
import unittest

from dfvfs.file_io import fake_file_io
from dfvfs.path import fake_path_spec
from dfvfs.resolver import context as dfvfs_context

from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import sccm

from tests.parsers.text_plugins import test_lib


def _ParseStringCompletesWithinTimeout(plugin, string, timeout=15.0):
    """Checks that parsing a string completes within a time budget.

    Args:
      plugin (TextPlugin): text log file plugin.
      string (str): string to parse.
      timeout (float): maximum number of seconds to wait.

    Returns:
      bool: True if parsing completed within the time budget.
    """

    def _Run():
        try:
            plugin._ParseString(string)  # pylint: disable=protected-access
        except errors.ParseError:
            pass

    thread = threading.Thread(target=_Run, daemon=True)
    thread.start()
    thread.join(timeout)
    return not thread.is_alive()


class SCCMTextPluginTest(test_lib.TextPluginTestCase):
    """Tests for the SCCM log text parser plugin."""

    # pylint: disable=protected-access

    def testCheckRequiredFormat(self):
        """Tests for the CheckRequiredFormat function."""
        plugin = sccm.SCCMTextPlugin()

        resolver_context = dfvfs_context.Context()
        test_path_spec = fake_path_spec.FakePathSpec(location="/file.txt")

        file_object = fake_file_io.FakeFile(
            resolver_context,
            test_path_spec,
            (
                b"<![LOG[    A user is logged on to the system.]LOG]!>"
                b'<time="19:33:19.766-330" date="11-28-2014" component="AppEnforce" '
                b'context="" type="1" thread="8744" file="appprovider.cpp:2083">\n'
            ),
        )
        file_object.Open()

        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        result = plugin.CheckRequiredFormat(None, text_reader)
        self.assertTrue(result)

        file_object = fake_file_io.FakeFile(
            resolver_context,
            test_path_spec,
            (
                b"(Microsoft.SoftwareCenter.Client.Data.Widget at Thingamabob)]LOG]!>"
                b'<time="10:22:50.8422964" date="1-2-2015" component="SCClient" '
                b'context="" type="0" thread="16" file="">\n'
            ),
        )
        file_object.Open()

        text_reader = text_parser.EncodedTextReader(file_object)
        text_reader.ReadLines()

        result = plugin.CheckRequiredFormat(None, text_reader)
        self.assertFalse(result)

    def testProcess(self):
        """Tests the Process function."""
        plugin = sccm.SCCMTextPlugin()
        storage_writer = self._ParseTextFileWithPlugin(["sccm_various.log"], plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 10)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        # Test log entry with milliseconds precision and time zone offset.
        # time="19:33:19.766-330" date="11-28-2014"
        expected_event_values = {
            "component": "AppEnforce",
            "data_type": "sccm_log:entry",
            "text": (
                '+++ Starting Install enforcement for App DT "Application '
                'Foo Version 2.2" ApplicationDeliveryType - ScopeId_AD87A846-'
                "E6A5-4088-875F-066CF1082D30/DeploymentType_14a11199-ee14-"
                "4c06-a5a7-68eadf501337, Revision - 10, ContentPath - "
                "C:\\Windows\\ccmcache\\u, Execution Context - System"
            ),
            "written_time": "2014-11-28T19:33:19.766-06:30",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

        # Test log entry with 100ns precision and time zone offset.
        # time="10:22:50.8422964" date="1-2-2015"
        expected_event_values = {
            "component": "SCClient",
            "data_type": "sccm_log:entry",
            "written_time": "2015-01-02T10:22:50.873496+00:00",
        }

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 3)
        self.CheckEventData(event_data, expected_event_values)

    def testParseLongLineCompletesInLinearTime(self):
        """Tests that a long line is parsed in bounded (linear) time."""
        plugin = sccm.SCCMTextPlugin()

        # Many record openers without a message terminator previously made the
        # message-text scan re-run to the end of the buffer at every opener
        # offset, so parsing was superlinear in the length of the input. It must
        # now complete quickly.
        long_text = "<![LOG[X" * 8000
        self.assertTrue(_ParseStringCompletesWithinTimeout(plugin, long_text))

        # A normal line still parses to the same fields.
        normal_line = (
            "<![LOG[A user is logged on.]LOG]!>"
            '<time="19:33:19.766-330" date="11-28-2014" '
            'component="AppEnforce" context="" type="1" thread="8744" '
            'file="appprovider.cpp:2083">\n'
        )
        key, structure, _, _ = plugin._ParseString(normal_line)
        self.assertEqual(key, "last_log_line")
        self.assertEqual(
            plugin._GetValueFromStructure(structure, "text"),
            "A user is logged on.",
        )
        self.assertEqual(
            plugin._GetValueFromStructure(structure, "component"), "AppEnforce"
        )


if __name__ == "__main__":
    unittest.main()
