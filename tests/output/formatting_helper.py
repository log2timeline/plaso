#!/usr/bin/env python3
"""Tests for the output module field formatting helper."""

import unittest

from acstore.containers import interface as containers_interface

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


class CountingFieldFormattingHelper(formatting_helper.FieldFormattingHelper):
    """Field formatter helper that counts the formatted fields."""

    _FIELD_FORMAT_CALLBACKS = {
        "display_name": "_FormatDisplayName",
        "message": "_FormatMessage",
        "message_short": "_FormatMessageShort",
        "zone": "_FormatTimeZone",
    }

    def __init__(self):
        """Initializes a field formatter helper that counts the formatted fields."""
        super().__init__()
        self.number_of_formatted_display_names = 0
        self.number_of_formatted_time_zones = 0

    def _FormatDisplayName(self, output_mediator, event, event_data, event_data_stream):
        """Formats the display name.

        Args:
          output_mediator (OutputMediator): mediates interactions between output
              modules and other components, such as storage and dfVFS.
          event (EventObject): event.
          event_data (EventData): event data.
          event_data_stream (EventDataStream): event data stream.

        Returns:
          str: display name field.
        """
        self.number_of_formatted_display_names += 1
        return super()._FormatDisplayName(
            output_mediator, event, event_data, event_data_stream
        )

    def _FormatTimeZone(self, output_mediator, event, event_data, event_data_stream):
        """Formats a time zone field.

        Args:
          output_mediator (OutputMediator): mediates interactions between output
              modules and other components, such as storage and dfVFS.
          event (EventObject): event.
          event_data (EventData): event data.
          event_data_stream (EventDataStream): event data stream.

        Returns:
          str: time zone field.
        """
        self.number_of_formatted_time_zones += 1
        return super()._FormatTimeZone(
            output_mediator, event, event_data, event_data_stream
        )


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

        # Test with timestamps near daylight saving time transitions.
        output_mediator.SetTimeZone("Europe/Brussels")

        test_values = [
            ("2024-03-31 00:30:00", "CET"),
            ("2024-03-31 01:30:00", "CEST"),
            ("2024-03-31 02:30:00", "CEST"),
            ("2024-10-27 00:30:00", "CEST"),
            ("2024-10-27 01:30:00", "CET"),
            ("2024-10-27 02:30:00", "CET"),
        ]
        for timestamp, expected_zone_string in test_values:
            event_values = dict(self._TEST_EVENTS[0])
            event_values["timestamp"] = timestamp
            event, event_data, event_data_stream = (
                containers_test_lib.CreateEventFromValues(event_values)
            )

            zone_string = test_helper._FormatTimeZone(
                output_mediator, event, event_data, event_data_stream
            )
            self.assertEqual(zone_string, expected_zone_string)

        # Test with a timestamp that overflows when converted to the time zone.
        event_values = dict(self._TEST_EVENTS[0])
        event_values["timestamp"] = "9999-12-31 23:30:00"
        event, event_data, event_data_stream = (
            containers_test_lib.CreateEventFromValues(event_values)
        )

        zone_string = test_helper._FormatTimeZone(
            output_mediator, event, event_data, event_data_stream
        )
        self.assertEqual(zone_string, "-")

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

    def testGetFormattedFieldWithCachedFieldValues(self):
        """Tests the GetFormattedField function with cached field values."""
        output_mediator = self._CreateOutputMediator()
        test_helper = CountingFieldFormattingHelper()

        event1, event_data1, event_data_stream1 = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )
        event_data1.SetIdentifier(
            containers_interface.AttributeContainerIdentifier(
                name="event_data", sequence_number=1
            )
        )
        test_event_values = dict(self._TEST_EVENTS[1])
        test_event_values["path_spec"] = fake_path_spec.FakePathSpec(
            location="log/syslog.2"
        )
        event2, event_data2, event_data_stream2 = (
            containers_test_lib.CreateEventFromValues(test_event_values)
        )
        event_data2.SetIdentifier(
            containers_interface.AttributeContainerIdentifier(
                name="event_data", sequence_number=2
            )
        )
        # A field that only depends on the event data is formatted once per event data.
        for _ in range(2):
            display_name_string = test_helper.GetFormattedField(
                output_mediator,
                "display_name",
                event1,
                event_data1,
                event_data_stream1,
                None,
            )
            self.assertEqual(display_name_string, "FAKE:log/syslog.1")

        self.assertEqual(test_helper.number_of_formatted_display_names, 1)

        display_name_string = test_helper.GetFormattedField(
            output_mediator,
            "display_name",
            event2,
            event_data2,
            event_data_stream2,
            None,
        )
        self.assertEqual(display_name_string, "FAKE:log/syslog.2")
        self.assertEqual(test_helper.number_of_formatted_display_names, 2)

        display_name_string = test_helper.GetFormattedField(
            output_mediator,
            "display_name",
            event1,
            event_data1,
            event_data_stream1,
            None,
        )
        self.assertEqual(display_name_string, "FAKE:log/syslog.1")
        self.assertEqual(test_helper.number_of_formatted_display_names, 2)

        # A field that depends on the event is not cached.
        for _ in range(2):
            zone_string = test_helper.GetFormattedField(
                output_mediator, "zone", event1, event_data1, event_data_stream1, None
            )
            self.assertEqual(zone_string, "UTC")

        self.assertEqual(test_helper.number_of_formatted_time_zones, 2)

        # Event data without an identifier is not cached.
        event3, event_data3, event_data_stream3 = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )
        for _ in range(2):
            display_name_string = test_helper.GetFormattedField(
                output_mediator,
                "display_name",
                event3,
                event_data3,
                event_data_stream3,
                None,
            )
            self.assertEqual(display_name_string, "FAKE:log/syslog.1")

        self.assertEqual(test_helper.number_of_formatted_display_names, 4)

    def testGetFormattedFieldWithCachedFieldValuesAndMessages(self):
        """Tests that field-value and event-value caches do not interfere."""
        formatters_directory_path = self._GetTestFilePath(["formatters"])

        output_mediator1 = self._CreateOutputMediator()
        output_mediator1.ReadMessageFormattersFromDirectory(formatters_directory_path)
        counting_helper1 = CountingEventFormatterHelper()
        output_mediator1.GetMessageFormatter("test:event").AddHelper(counting_helper1)

        test_helper = CountingFieldFormattingHelper()

        event1, event_data1, event_data_stream1 = (
            containers_test_lib.CreateEventFromValues(self._TEST_EVENTS[0])
        )
        event_data1.SetIdentifier(
            containers_interface.AttributeContainerIdentifier(
                name="event_data", sequence_number=1
            )
        )

        test_event_values2 = dict(self._TEST_EVENTS[1])
        test_event_values2["path_spec"] = fake_path_spec.FakePathSpec(
            location="log/syslog.2"
        )
        test_event_values2["text"] = "Second test event message"
        event2, event_data2, event_data_stream2 = (
            containers_test_lib.CreateEventFromValues(test_event_values2)
        )
        event_data2.SetIdentifier(
            containers_interface.AttributeContainerIdentifier(
                name="event_data", sequence_number=2
            )
        )

        # Formatting another cached field before message must not cause a false
        # cache hit in _GetFormattedEventValues.
        display_name = test_helper.GetFormattedField(
            output_mediator1,
            "display_name",
            event1,
            event_data1,
            event_data_stream1,
            None,
        )
        self.assertEqual(display_name, "FAKE:log/syslog.1")

        expected_message1 = (
            "Reporter <CRON> PID: 8442 (pam_unix(cron:session): session closed "
            "for user root)"
        )
        message1 = test_helper.GetFormattedField(
            output_mediator1, "message", event1, event_data1, event_data_stream1, None
        )
        message_short1 = test_helper.GetFormattedField(
            output_mediator1,
            "message_short",
            event1,
            event_data1,
            event_data_stream1,
            None,
        )
        self.assertEqual(message1, expected_message1)
        self.assertEqual(message_short1, expected_message1)
        self.assertEqual(counting_helper1.number_of_calls, 1)

        # Formatting a second event must not reuse stale formatted event values.
        display_name2 = test_helper.GetFormattedField(
            output_mediator1,
            "display_name",
            event2,
            event_data2,
            event_data_stream2,
            None,
        )
        message2 = test_helper.GetFormattedField(
            output_mediator1, "message", event2, event_data2, event_data_stream2, None
        )
        message_short2 = test_helper.GetFormattedField(
            output_mediator1,
            "message_short",
            event2,
            event_data2,
            event_data_stream2,
            None,
        )
        self.assertEqual(display_name2, "FAKE:log/syslog.2")
        self.assertEqual(message2, "Second test event message")
        self.assertEqual(message_short2, "Second test event message")
        self.assertEqual(counting_helper1.number_of_calls, 2)

        # Calling _FormatMessage directly must not pollute the field-values cache.
        direct_message1 = test_helper._FormatMessage(
            output_mediator1, event1, event_data1, event_data_stream1
        )
        self.assertEqual(direct_message1, expected_message1)

        cached_display_name2 = test_helper.GetFormattedField(
            output_mediator1,
            "display_name",
            event2,
            event_data2,
            event_data_stream2,
            None,
        )
        self.assertEqual(cached_display_name2, "FAKE:log/syslog.2")
        self.assertEqual(test_helper.number_of_formatted_display_names, 2)

        # Unstored event data still shares formatted event values across message
        # and message_short without failing after another cached field.
        test_event_values3 = dict(self._TEST_EVENTS[0])
        test_event_values3["text"] = "Third unstored event message"
        event3, event_data3, event_data_stream3 = (
            containers_test_lib.CreateEventFromValues(test_event_values3)
        )
        test_helper.GetFormattedField(
            output_mediator1,
            "display_name",
            event3,
            event_data3,
            event_data_stream3,
            None,
        )
        message3 = test_helper.GetFormattedField(
            output_mediator1, "message", event3, event_data3, event_data_stream3, None
        )
        message_short3 = test_helper.GetFormattedField(
            output_mediator1,
            "message_short",
            event3,
            event_data3,
            event_data_stream3,
            None,
        )
        self.assertEqual(message3, "Third unstored event message")
        self.assertEqual(message_short3, "Third unstored event message")
        self.assertEqual(counting_helper1.number_of_calls, 4)

        # Switching output_mediator invalidates both caches.
        output_mediator2 = self._CreateOutputMediator()
        output_mediator2.ReadMessageFormattersFromDirectory(formatters_directory_path)
        counting_helper2 = CountingEventFormatterHelper()
        output_mediator2.GetMessageFormatter("test:event").AddHelper(counting_helper2)

        display_name1_new = test_helper.GetFormattedField(
            output_mediator2,
            "display_name",
            event1,
            event_data1,
            event_data_stream1,
            None,
        )
        message1_new = test_helper.GetFormattedField(
            output_mediator2, "message", event1, event_data1, event_data_stream1, None
        )
        self.assertEqual(display_name1_new, "FAKE:log/syslog.1")
        self.assertEqual(message1_new, expected_message1)
        self.assertEqual(test_helper.number_of_formatted_display_names, 4)
        self.assertEqual(counting_helper2.number_of_calls, 1)


class FormattedEventValuesCacheTest(test_lib.OutputModuleTestCase):
    """Tests for the formatted event values cache."""

    # pylint: disable=protected-access

    def testGetAndSet(self):
        """Tests the Get and Set functions."""
        cache = formatting_helper._FormattedEventValuesCache()
        output_mediator1 = self._CreateOutputMediator()
        output_mediator2 = self._CreateOutputMediator()

        event_data1 = events.EventData()
        event_data2 = events.EventData()

        self.assertEqual(cache.Get(output_mediator1, event_data1), (None, None))
        self.assertEqual(cache.Get(None, None), (None, None))

        formatter = formatting_helper.FieldFormattingHelper._DEFAULT_MESSAGE_FORMATTER
        event_values = {"text": "test"}
        cache.Set(output_mediator1, event_data1, formatter, event_values)

        self.assertEqual(
            cache.Get(output_mediator1, event_data1), (formatter, event_values)
        )
        self.assertEqual(cache.Get(output_mediator1, event_data2), (None, None))
        self.assertEqual(cache.Get(output_mediator2, event_data1), (None, None))


class FormattedFieldValuesCacheTest(test_lib.OutputModuleTestCase):
    """Tests for the formatted field values cache."""

    # pylint: disable=protected-access

    def testGetFieldValues(self):
        """Tests the GetFieldValues function."""
        cache = formatting_helper._FormattedFieldValuesCache(
            maximum_number_of_entries=2
        )
        output_mediator1 = self._CreateOutputMediator()
        output_mediator2 = self._CreateOutputMediator()

        # None and unstored event data are not cached.
        self.assertIsNone(cache.GetFieldValues(output_mediator1, None))

        unstored_event_data = events.EventData()
        self.assertIsNone(cache.GetFieldValues(output_mediator1, unstored_event_data))

        # Incomplete identifiers (CopyToString() is None) are not cached.
        incomplete_event_data = events.EventData()
        incomplete_event_data.SetIdentifier(
            containers_interface.AttributeContainerIdentifier(
                name="event_data", sequence_number=None
            )
        )
        self.assertIsNone(cache.GetFieldValues(output_mediator1, incomplete_event_data))

        # Stored event data is cached by identifier and evicted past the limit.
        event_data1 = events.EventData()
        event_data1.SetIdentifier(
            containers_interface.AttributeContainerIdentifier(
                name="event_data", sequence_number=1
            )
        )
        event_data2 = events.EventData()
        event_data2.SetIdentifier(
            containers_interface.AttributeContainerIdentifier(
                name="event_data", sequence_number=2
            )
        )
        event_data3 = events.EventData()
        event_data3.SetIdentifier(
            containers_interface.AttributeContainerIdentifier(
                name="event_data", sequence_number=3
            )
        )

        field_values1 = cache.GetFieldValues(output_mediator1, event_data1)
        self.assertIsNotNone(field_values1)
        field_values1["display_name"] = "one"

        self.assertIs(
            cache.GetFieldValues(output_mediator1, event_data1), field_values1
        )

        field_values2 = cache.GetFieldValues(output_mediator1, event_data2)
        self.assertIsNotNone(field_values2)
        self.assertIs(
            cache.GetFieldValues(output_mediator1, event_data1), field_values1
        )

        # Adding a third entry clears the cache when limit is 2.
        field_values3 = cache.GetFieldValues(output_mediator1, event_data3)
        self.assertIsNotNone(field_values3)
        self.assertNotIn("event_data.1", cache._field_values_per_event_data)

        # Switching output_mediator clears cached entries and handles None safely.
        self.assertIsNone(cache.GetFieldValues(output_mediator2, None))
        self.assertEqual(cache._field_values_per_event_data, {})


if __name__ == "__main__":
    unittest.main()
