#!/usr/bin/env python3
"""Tests for the timeliner configuration file."""

import unittest

# Import the parsers like the extraction tools do, which also imports all the
# event data that can be produced during extraction.
from plaso import parsers  # pylint: disable=unused-import
from plaso.containers import events
from plaso.engine import yaml_timeliner_file

from tests import test_lib as shared_test_lib


class TimelinerDataTest(shared_test_lib.BaseTestCase):
    """Tests the timeliner.yaml file."""

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

    def testAttributeMappings(self):
        """Tests that the attribute mappings refer to event data attributes."""
        timeliner_file_path = self._GetDataFilePath(["timeliner.yaml"])
        timeliner_file = yaml_timeliner_file.YAMLTimelinerConfigurationFile()

        classes_per_data_type = self._GetEventDataClassesPerDataType()

        issues = []
        for timeliner_definition in timeliner_file.ReadFromFile(timeliner_file_path):
            data_type = timeliner_definition.data_type

            event_data_classes = classes_per_data_type.get(data_type, set())
            if not event_data_classes:
                issues.append(f"{data_type:s}: no corresponding event data")
                continue

            for event_data_class in sorted(
                event_data_classes, key=lambda cls: (cls.__module__, cls.__name__)
            ):
                try:
                    event_data = event_data_class()
                except TypeError:
                    # Event data that cannot be instantiated without arguments is
                    # reported by utils/export_event_data.py.
                    continue

                # The timeliner processes event data that was read back from storage,
                # which only contains the attributes of the instance.
                attribute_names = set(event_data.GetAttributeNames())
                for attribute_name in sorted(timeliner_definition.attribute_mappings):
                    if attribute_name not in attribute_names:
                        issues.append(
                            f"{data_type:s}: attribute: {attribute_name:s} not "
                            f"defined by: {event_data_class.__name__:s}"
                        )

        self.assertEqual(issues, [])


if __name__ == "__main__":
    unittest.main()
