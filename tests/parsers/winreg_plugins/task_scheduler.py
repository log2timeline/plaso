#!/usr/bin/env python3
"""Tests for the Task Scheduler Windows Registry plugin."""

import unittest

from dfwinreg import definitions as dfwinreg_definitions
from dfwinreg import fake as dfwinreg_fake

from plaso.parsers.winreg_plugins import task_scheduler

from tests.parsers.winreg_plugins import test_lib


class TaskCacheWindowsRegistryPluginTest(test_lib.RegistryPluginTestCase):
    """Tests for the Task Cache key Windows Registry plugin."""

    _TASK_IDENTIFIER = "{044A6734-E90E-4F8F-B357-B2DC8AB3B5EC}"

    def _CreateTestKey(self, id_value_data, id_value_data_type):
        """Creates Registry keys and values for testing.

        Args:
          id_value_data (bytes): data of the "Id" value of the task in the Tree key.
          id_value_data_type (int): data type of the "Id" value.

        Returns:
          dfwinreg.WinRegistryKey: a Windows Registry key.
        """
        registry_key = dfwinreg_fake.FakeWinRegistryKey(
            "TaskCache",
            key_path_prefix="HKEY_LOCAL_MACHINE\\Software",
            relative_key_path=(
                "Microsoft\\Windows NT\\CurrentVersion\\Schedule\\TaskCache"
            ),
        )

        tasks_key = dfwinreg_fake.FakeWinRegistryKey("Tasks")
        registry_key.AddSubkey(tasks_key.name, tasks_key)

        task_key = dfwinreg_fake.FakeWinRegistryKey(self._TASK_IDENTIFIER)
        tasks_key.AddSubkey(task_key.name, task_key)

        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "DynamicInfo",
            data=b"\x03\x00\x00\x00" + b"\x00" * 24,
            data_type=dfwinreg_definitions.REG_BINARY,
        )
        task_key.AddValue(registry_value)

        tree_key = dfwinreg_fake.FakeWinRegistryKey("Tree")
        registry_key.AddSubkey(tree_key.name, tree_key)

        tree_task_key = dfwinreg_fake.FakeWinRegistryKey("SynchronizeTime")
        tree_key.AddSubkey(tree_task_key.name, tree_task_key)

        registry_value = dfwinreg_fake.FakeWinRegistryValue(
            "Id", data=id_value_data, data_type=id_value_data_type
        )
        tree_task_key.AddValue(registry_value)

        return registry_key

    def _ParseTestKey(self, id_value_data, id_value_data_type):
        """Parses a test key with the plugin.

        Args:
          id_value_data (bytes): data of the "Id" value of the task in the Tree key.
          id_value_data_type (int): data type of the "Id" value.

        Returns:
          tuple[str, int]: task name of the event data and number of extraction
              warnings.
        """
        registry_key = self._CreateTestKey(id_value_data, id_value_data_type)
        plugin = task_scheduler.TaskCacheWindowsRegistryPlugin()
        storage_writer = self._ParseKeyWithPlugin(registry_key, plugin)

        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 1)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )

        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        return event_data.task_name, number_of_warnings

    def testFilters(self):
        """Tests the FILTERS class attribute."""
        plugin = task_scheduler.TaskCacheWindowsRegistryPlugin()

        self._AssertFiltersOnKeyPath(
            plugin,
            "HKEY_LOCAL_MACHINE\\Software",
            "Microsoft\\Windows NT\\CurrentVersion\\Schedule\\TaskCache",
        )
        self._AssertNotFiltersOnKeyPath(plugin, "HKEY_LOCAL_MACHINE\\Software", "Bogus")

    def testProcess(self):
        """Tests the Process function."""
        test_file_entry = self._GetTestFileEntry(["SOFTWARE-RunTests"])
        key_path = (
            "HKEY_LOCAL_MACHINE\\Software\\Microsoft\\Windows NT\\CurrentVersion\\"
            "Schedule\\TaskCache"
        )
        plugin = task_scheduler.TaskCacheWindowsRegistryPlugin()

        storage_writer = self._ParseKeyPathWithFileEntry(
            test_file_entry,
            key_path,
            plugin,
        )
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers(
            "event_data"
        )
        self.assertEqual(number_of_event_data, 85)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "extraction_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        number_of_warnings = storage_writer.GetNumberOfAttributeContainers(
            "recovery_warning"
        )
        self.assertEqual(number_of_warnings, 0)

        task_key_path = "\\".join(
            [key_path, "Tasks", "{044A6734-E90E-4F8F-B357-B2DC8AB3B5EC}"]
        )
        expected_event_values = {
            "data_type": "windows:registry:task_scheduler:task_cache:entry",
            "key_path": task_key_path,
            "last_registered_time": "2009-07-14T05:08:50.8116269+00:00",
            "last_written_time": "2011-08-15T08:54:09.0468750+00:00",
            "launch_time": None,
            "task_name": "SynchronizeTime",
            "task_identifier": "{044A6734-E90E-4F8F-B357-B2DC8AB3B5EC}",
            "unknown_time": None,
        }
        event_data = storage_writer.GetAttributeContainerByIndex("event_data", 0)
        self.CheckEventData(event_data, expected_event_values)

    def testProcessWithIdValueWithoutEndOfStringCharacter(self):
        """Tests the Process function with an "Id" value of an unexpected size."""
        # The "Id" value contains a GUID string but is 76 instead of 78 bytes in
        # size, which is expected to map the task name with a warning.
        task_name, number_of_warnings = self._ParseTestKey(
            self._TASK_IDENTIFIER.encode("utf-16-le"), dfwinreg_definitions.REG_SZ
        )
        self.assertEqual(task_name, "SynchronizeTime")
        self.assertEqual(number_of_warnings, 1)

    def testProcessWithIdValueNotContainingGUID(self):
        """Tests the Process function with an "Id" value that is not a GUID."""
        # The "Id" value is 78 bytes in size but does not contain a GUID string.
        id_value_data = "{044A6734-E90E-4F8F-B357-B2DC8AB3B5EX}".encode("utf-16-le")
        self.assertEqual(len(id_value_data), 76)

        task_name, number_of_warnings = self._ParseTestKey(
            id_value_data + b"\x00\x00", dfwinreg_definitions.REG_SZ
        )
        self.assertEqual(task_name, self._TASK_IDENTIFIER)
        self.assertEqual(number_of_warnings, 1)

        # The "Id" value contains a GUID string without curly brackets.
        task_name, number_of_warnings = self._ParseTestKey(
            self._TASK_IDENTIFIER[1:-1].encode("utf-16-le"),
            dfwinreg_definitions.REG_SZ,
        )
        self.assertEqual(task_name, self._TASK_IDENTIFIER)
        self.assertEqual(number_of_warnings, 2)

    def testProcessWithIdValueNotString(self):
        """Tests the Process function with an "Id" value that is not a string."""
        # The "Id" value is 78 bytes in size but is not stored as a string.
        id_value_data = self._TASK_IDENTIFIER.encode("utf-16-le") + b"\x00\x00"
        self.assertEqual(len(id_value_data), 78)

        task_name, number_of_warnings = self._ParseTestKey(
            id_value_data, dfwinreg_definitions.REG_BINARY
        )
        self.assertEqual(task_name, self._TASK_IDENTIFIER)
        self.assertEqual(number_of_warnings, 1)


if __name__ == "__main__":
    unittest.main()
