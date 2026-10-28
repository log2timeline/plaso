#!/usr/bin/env python3
"""Tests for the formatters configuration files."""

import glob
import os
import unittest

import yaml

# Import the parsers like the extraction tools do, which also imports all the
# event data that can be produced during extraction.
from plaso import parsers  # pylint: disable=unused-import
from plaso.containers import events
from plaso.formatters import interface

from tests import test_lib as shared_test_lib


class FormattersDataTest(shared_test_lib.BaseTestCase):
    """Tests the formatters configuration files."""

    # Show all the issues when the test fails.
    maxDiff = None

    _HELPER_KEYS = (
        "boolean_helpers",
        "custom_helpers",
        "enumeration_helpers",
        "flags_helpers",
    )

    _MESSAGE_KEYS = ("message", "short_message")

    # pylint: disable=protected-access
    _ATTRIBUTE_NAME_RE = interface.EventFormatter._FORMAT_STRING_ATTRIBUTE_NAME_RE

    def _GetEventDataClassesPerDataType(self):
        """Retrieves the Plaso event data classes per data type.

        Returns:
          dict[str, set[type]]: event data classes per data type.
        """
        classes_per_data_type = {}

        classes = list(events.EventData.__subclasses__())
        while classes:
            event_data_class = classes.pop()
            classes.extend(event_data_class.__subclasses__())

            # Only consider event data classes that are part of Plaso, not those
            # defined by tests, and that define their own data type, not base
            # classes that inherit the data type of their parent.
            if (
                event_data_class.__module__.startswith("plaso.")
                and "DATA_TYPE" in event_data_class.__dict__
            ):
                data_type = event_data_class.DATA_TYPE
                classes_per_data_type.setdefault(data_type, set()).add(event_data_class)

        return classes_per_data_type

    def _GetFormatStringAttributeNames(self, formatter_definition, message_key):
        """Retrieves the attribute names used by a message of a formatter.

        Args:
          formatter_definition (dict[str, object]): formatter definition.
          message_key (str): key of the message in the formatter definition.

        Returns:
          set[str]: attribute names used by the message, except for those that are
              provided by the formatter helpers.
        """
        format_string_pieces = formatter_definition.get(message_key) or []
        if isinstance(format_string_pieces, str):
            format_string_pieces = [format_string_pieces]

        attribute_names = set()
        for format_string_piece in format_string_pieces:
            attribute_names.update(self._ATTRIBUTE_NAME_RE.findall(format_string_piece))

        for helper_key in self._HELPER_KEYS:
            for helper_definition in formatter_definition.get(helper_key) or []:
                attribute_names.discard(helper_definition.get("output_attribute"))

        return attribute_names

    def testAttributeNames(self):
        """Tests that the formatters refer to event data attributes."""
        formatters_path = self._GetDataFilePath(["formatters"])

        classes_per_data_type = self._GetEventDataClassesPerDataType()

        issues = []
        for path in sorted(glob.glob(os.path.join(formatters_path, "*.yaml"))):
            filename = os.path.basename(path)

            with open(path, encoding="utf-8") as file_object:
                formatter_definitions = list(yaml.safe_load_all(file_object))

            for formatter_definition in formatter_definitions:
                if not formatter_definition:
                    continue

                data_type = formatter_definition.get("data_type")

                event_data_classes = classes_per_data_type.get(data_type, set())
                if not event_data_classes:
                    issues.append(
                        f"{filename:s}: {data_type:s}: no corresponding event data"
                    )
                    continue

                for event_data_class in sorted(
                    event_data_classes, key=lambda cls: (cls.__module__, cls.__name__)
                ):
                    try:
                        event_data = event_data_class()
                    except TypeError:
                        # Event data that cannot be instantiated without arguments is
                        # reported by utils/export_event_data.py.
                        # TODO: remove this exception and fail instead, once all event
                        # data can be instantiated without arguments.
                        continue

                    # The formatters format event data that was read back from
                    # storage, which only contains the attributes of the instance.
                    event_data_attribute_names = set(event_data.GetAttributeNames())

                    for message_key in self._MESSAGE_KEYS:
                        attribute_names = self._GetFormatStringAttributeNames(
                            formatter_definition, message_key
                        )
                        for attribute_name in sorted(
                            attribute_names - event_data_attribute_names
                        ):
                            issues.append(
                                f"{filename:s}: {data_type:s}: {message_key:s}: "
                                f"attribute: {attribute_name:s} not defined by: "
                                f"{event_data_class.__name__:s}"
                            )

        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
