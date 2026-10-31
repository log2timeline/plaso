#!/usr/bin/env python3
"""Tests for the output module field formatting helper."""

import unittest

from dfdatetime import filetime as dfdatetime_filetime
from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import semantic_time as dfdatetime_semantic_time

from dfvfs.path import fake_path_spec

from plaso.containers import events
from plaso.formatters import interface as formatters_interface
from plaso.lib import definitions
from plaso.output import formatting_helper

from tests.containers import test_lib as containers_test_lib
from tests.output import test_lib


class CountingEventFormatterHelper(formatters_interface.EventFormatterHelper):
    """Event formatter helper that counts its invocations for testing purposes.

    Attributes:
      number_of_calls (int): number of times FormatEventValues was called.
    """

    def __init__(self):
        """Initializes a counting event formatter helper."""
        super().__init__()
        self.number_of_calls = 0

    def FormatEventValues(self, output_mediator, event_values):
        """Formats event values using the helper.

        Args:
          output_mediator (OutputMediator): output mediator.
          event_values (dict[str, object]): event values.
        """
        self.number_of_calls += 1


class TestFieldFormattingHelper(formatting_helper.FieldFormattingHelper):
    """Field formatter helper for testing purposes."""

    _FIELD_FORMAT_CALLBACKS = {"zone": "_FormatTimeZone"}


class FieldFormattingHelperTest(test_lib.OutputModuleTestCase):
    """Test the output module field formatting helper."""

    # pylint: disable=protected-access

    _TEST_EVENTS = [
        {
            "data_type": "test:event",
            "filename": "log/syslog.1",
            "hostname": "ubuntu",
            "path_spec": fake_path_spec.FakePathSpec(location="log/syslog.1"),
            "text": (
                "Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n "
                "closed for user root)"
            ),
            "timestamp": "2012-06-27 18:17:01",
            "timestamp_desc": definitions.TIME_DESCRIPTION_METADATA_MODIFICATION,
        },
        {
            "data_type": "test:event",
            "filename": "log/syslog.1",
            "hostname": "ubuntu",
            "path_spec": fake_path_spec.FakePathSpec(location="log/syslog.1"),
            "text": (
                "Reporter <CRON> PID: 8442 (pam_unix(cron:session): session\n "
                "closed for user root)"
            ),
            "timestamp": "2012-06-27 20:17:01",
            "timestamp_desc": definitions.TIME_DESCRIPTION_METADATA_MODIFICATION,
        },
    ]

    def testFormatDateTime(self):
        """Tests the _FormatDateTime function with dynamic time."""
        output_mediator = self._CreateOutputMediator(dynamic_time=True)
        test_helper = formatting_helper.FieldFormattingHelper()

        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )

        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "2012-06-27T18:17:01.000000+00:00")

        output_mediator.SetTimeZone("Europe/Amsterdam")

        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "2012-06-27T20:17:01.000000+02:00")

        output_mediator.SetTimeZone("UTC")

        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[1])
        )
        event.date_time._time_zone_offset = 120

        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "2012-06-27T18:17:01.000000+00:00")

        event.date_time = dfdatetime_semantic_time.InvalidTime()

        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "Invalid")

        # Test with event.is_local_time
        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )
        event.timestamp -= 120 * 60 * 1000000
        event.date_time.is_local_time = True

        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "2012-06-27T16:17:01.000000+00:00")

    def testFormatDateTimeWithoutDynamicTime(self):
        """Tests the _FormatDateTime function without dynamic time."""
        output_mediator = self._CreateOutputMediator(dynamic_time=False)
        test_helper = formatting_helper.FieldFormattingHelper()

        # Test with event.date_time
        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )

        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "2012-06-27T18:17:01.000000+00:00")

        output_mediator.SetTimeZone("Europe/Amsterdam")

        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "2012-06-27T20:17:01.000000+02:00")

        output_mediator.SetTimeZone("UTC")

        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[1])
        )
        event.date_time._time_zone_offset = 120

        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "2012-06-27T18:17:01.000000+00:00")

        event.date_time = dfdatetime_posix_time.PosixTimeInMilliseconds(
            timestamp=-1567517139327
        )

        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "1920-04-30T10:34:20.673000+00:00")

        event.date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
            timestamp=-1567517139327447
        )

        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "1920-04-30T10:34:20.672553+00:00")

        event.date_time = dfdatetime_posix_time.PosixTimeInNanoseconds(
            timestamp=-1567517139327447871
        )

        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "1920-04-30T10:34:20.672552+00:00")

        # Test with a fraction of second that has leading zeros.
        event.date_time = dfdatetime_posix_time.PosixTimeInMilliseconds(
            timestamp=1340821021005
        )

        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "2012-06-27T18:17:01.005000+00:00")

        event.date_time = dfdatetime_posix_time.PosixTimeInMilliseconds(
            timestamp=-1567517139005
        )

        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "1920-04-30T10:34:20.995000+00:00")

        event.date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
            timestamp=1340821021012345
        )

        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "2012-06-27T18:17:01.012345+00:00")

        event.date_time = dfdatetime_filetime.Filetime(timestamp=129852946210123456)

        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "2012-06-27T18:17:01.012346+00:00")

        event.date_time = dfdatetime_semantic_time.InvalidTime()

        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "0000-00-00T00:00:00.000000+00:00")

        # Test with event.is_local_time
        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )
        event.timestamp -= 120 * 60 * 1000000
        event.date_time.is_local_time = True

        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "2012-06-27T16:17:01.000000+00:00")

        # Test with event.timestamp
        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )
        event.date_time = None

        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "2012-06-27T18:17:01.000000+00:00")

        event.timestamp = 0
        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "0000-00-00T00:00:00.000000+00:00")

        event.timestamp = -1567517139327447
        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "1920-04-30T10:34:20.672553+00:00")

        event.timestamp = -9223372036854775808
        date_time_string = test_helper._FormatDateTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(date_time_string, "0000-00-00T00:00:00.000000+00:00")

    def testFormatDisplayName(self):
        """Tests the _FormatDisplayName function."""
        output_mediator = self._CreateOutputMediator()
        test_helper = formatting_helper.FieldFormattingHelper()

        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )
        display_name_string = test_helper._FormatDisplayName(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(display_name_string, "FAKE:log/syslog.1")

    def testFormatFilename(self):
        """Tests the _FormatFilename function."""
        output_mediator = self._CreateOutputMediator()
        test_helper = formatting_helper.FieldFormattingHelper()

        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )
        filename_string = test_helper._FormatFilename(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(filename_string, "log/syslog.1")

    def testFormatHostname(self):
        """Tests the _FormatHostname function."""
        output_mediator = self._CreateOutputMediator()
        test_helper = formatting_helper.FieldFormattingHelper()

        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )
        hostname_string = test_helper._FormatHostname(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(hostname_string, "ubuntu")

    def testFormatInode(self):
        """Tests the _FormatInode function."""
        output_mediator = self._CreateOutputMediator()
        test_helper = formatting_helper.FieldFormattingHelper()

        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )
        inode_string = test_helper._FormatInode(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(inode_string, "-")

    def testFormatMACB(self):
        """Tests the _FormatMACB function."""
        output_mediator = self._CreateOutputMediator()
        test_helper = formatting_helper.FieldFormattingHelper()

        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )
        macb_string = test_helper._FormatMACB(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(macb_string, "..C.")

    def testFormatMessage(self):
        """Tests the _FormatMessage function."""
        output_mediator = self._CreateOutputMediator()

        formatters_directory_path = self._GetTestFilePath(["formatters"])
        output_mediator.ReadMessageFormattersFromDirectory(formatters_directory_path)

        test_helper = formatting_helper.FieldFormattingHelper()

        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )

        message_string = test_helper._FormatMessage(
            output_mediator, event, event_data, event_data_stream
        )

        expected_message_string = (
            "Reporter <CRON> PID: 8442 (pam_unix(cron:session): session closed "
            "for user root)"
        )
        self.assertEqual(message_string, expected_message_string)

    def testFormatMessageShort(self):
        """Tests the _FormatMessageShort function."""
        output_mediator = self._CreateOutputMediator()

        formatters_directory_path = self._GetTestFilePath(["formatters"])
        output_mediator.ReadMessageFormattersFromDirectory(formatters_directory_path)

        test_helper = formatting_helper.FieldFormattingHelper()

        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )

        message_short_string = test_helper._FormatMessageShort(
            output_mediator, event, event_data, event_data_stream
        )

        expected_message_short_string = (
            "Reporter <CRON> PID: 8442 (pam_unix(cron:session): session closed "
            "for user root)"
        )
        self.assertEqual(message_short_string, expected_message_short_string)

    def testFormatMessageAndMessageShortFormatEventValuesOnce(self):
        """Tests that the message fields format the event values once."""
        output_mediator = self._CreateOutputMediator()

        formatters_directory_path = self._GetTestFilePath(["formatters"])
        output_mediator.ReadMessageFormattersFromDirectory(formatters_directory_path)

        counting_helper = CountingEventFormatterHelper()
        message_formatter = output_mediator.GetMessageFormatter("test:event")
        message_formatter.AddHelper(counting_helper)

        test_helper = formatting_helper.FieldFormattingHelper()

        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )

        message_string = test_helper._FormatMessage(
            output_mediator, event, event_data, event_data_stream
        )
        message_short_string = test_helper._FormatMessageShort(
            output_mediator, event, event_data, event_data_stream
        )

        expected_message_string = (
            "Reporter <CRON> PID: 8442 (pam_unix(cron:session): session closed "
            "for user root)"
        )
        self.assertEqual(message_string, expected_message_string)
        self.assertEqual(message_short_string, expected_message_string)
        self.assertEqual(counting_helper.number_of_calls, 1)

        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[1])
        )

        test_helper._FormatMessage(
            output_mediator, event, event_data, event_data_stream
        )
        test_helper._FormatMessageShort(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(counting_helper.number_of_calls, 2)

    def testFormatSource(self):
        """Tests the _FormatSource function."""
        output_mediator = self._CreateOutputMediator()

        formatters_directory_path = self._GetTestFilePath(["formatters"])
        output_mediator.ReadMessageFormattersFromDirectory(formatters_directory_path)

        test_helper = formatting_helper.FieldFormattingHelper()

        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )

        source_string = test_helper._FormatSource(
            output_mediator, event, event_data, event_data_stream
        )

        self.assertEqual(source_string, "Test log file")

    def testFormatSourceShort(self):
        """Tests the _FormatSourceShort function."""
        output_mediator = self._CreateOutputMediator()

        formatters_directory_path = self._GetTestFilePath(["formatters"])
        output_mediator.ReadMessageFormattersFromDirectory(formatters_directory_path)

        test_helper = formatting_helper.FieldFormattingHelper()

        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )

        source_short_string = test_helper._FormatSourceShort(
            output_mediator, event, event_data, event_data_stream
        )

        self.assertEqual(source_short_string, "FILE")

    def testFormatTag(self):
        """Tests the _FormatTag function."""
        output_mediator = self._CreateOutputMediator()
        test_helper = formatting_helper.FieldFormattingHelper()

        tag_string = test_helper._FormatTag(output_mediator, None)
        self.assertEqual(tag_string, "-")

        event_tag = events.EventTag()
        event_tag.AddLabel("one")
        event_tag.AddLabel("two")

        tag_string = test_helper._FormatTag(output_mediator, event_tag)
        self.assertEqual(tag_string, "one two")

    def testFormatTime(self):
        """Tests the _FormatTime function."""
        output_mediator = self._CreateOutputMediator()
        test_helper = formatting_helper.FieldFormattingHelper()

        # Test with event.date_time
        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )

        time_string = test_helper._FormatTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(time_string, "18:17:01")

        output_mediator.SetTimeZone("Europe/Amsterdam")

        time_string = test_helper._FormatTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(time_string, "20:17:01")

        output_mediator.SetTimeZone("UTC")

        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[1])
        )
        event.date_time._time_zone_offset = 120

        time_string = test_helper._FormatTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(time_string, "18:17:01")

        # Test with event.is_local_time
        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )
        event.timestamp -= 120 * 60 * 1000000
        event.date_time.is_local_time = True

        time_string = test_helper._FormatTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(time_string, "16:17:01")

        # Test with event.timestamp
        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )
        event.date_time = None

        time_string = test_helper._FormatTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(time_string, "18:17:01")

        event.timestamp = 0
        time_string = test_helper._FormatTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(time_string, "--:--:--")

        event.timestamp = -9223372036854775808
        time_string = test_helper._FormatTime(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(time_string, "--:--:--")

    def testFormatTimeZone(self):
        """Tests the _FormatTimeZone function."""
        output_mediator = self._CreateOutputMediator()
        test_helper = formatting_helper.FieldFormattingHelper()

        # Test with event.date_time
        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )

        zone_string = test_helper._FormatTimeZone(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(zone_string, "UTC")

        output_mediator.SetTimeZone("Europe/Amsterdam")

        zone_string = test_helper._FormatTimeZone(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(zone_string, "CEST")

        output_mediator.SetTimeZone("UTC")

        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[1])
        )
        event.date_time._time_zone_offset = 120

        zone_string = test_helper._FormatTimeZone(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(zone_string, "UTC")

        # Test with event.is_local_time
        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )
        event.timestamp -= 120 * 60 * 1000000
        event.date_time.is_local_time = True

        zone_string = test_helper._FormatTimeZone(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(zone_string, "UTC")

    def testFormatUsername(self):
        """Tests the _FormatUsername function."""
        output_mediator = self._CreateOutputMediator()
        test_helper = formatting_helper.FieldFormattingHelper()

        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )
        username_string = test_helper._FormatUsername(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(username_string, "-")

    def testReportEventError(self):
        """Tests the _ReportEventError function."""
        test_helper = formatting_helper.FieldFormattingHelper()

        event, event_data, _ = containers_test_lib.CreateEventFromValues(
            self._TEST_EVENTS[0]
        )
        event_identifier = event.GetIdentifier()
        event_identifier_string = event_identifier.CopyToString()
        event_data._parser_chain = "test_parser"

        with self.assertLogs("output", level="ERROR") as context_manager:
            test_helper._ReportEventError(event, event_data, "test error")

        expected_message = (
            f"Event: {event_identifier_string:s} description: Metadata "
            f"Modification Time data type: test:event display name: N/A "
            f"parser chain: test_parser with error: test error"
        )
        self.assertEqual(len(context_manager.records), 1)
        self.assertEqual(context_manager.records[0].getMessage(), expected_message)

    def testGetFormattedField(self):
        """Tests the GetFormattedField function."""
        output_mediator = self._CreateOutputMediator()
        test_helper = TestFieldFormattingHelper()

        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )
        zone_string = test_helper.GetFormattedField(
            output_mediator, "zone", event, event_data, event_data_stream, None
        )
        self.assertEqual(zone_string, "UTC")


if __name__ == "__main__":
    unittest.main()
