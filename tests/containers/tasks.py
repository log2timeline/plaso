#!/usr/bin/env python3
"""Tests for the tasks attribute containers."""

import unittest
import uuid

from plaso.containers import tasks

from tests import test_lib as shared_test_lib


class TaskTest(shared_test_lib.BaseTestCase):
    """Tests for the task attribute container."""

    def testGetAttributeNames(self):
        """Tests the GetAttributeNames function."""
        session_identifier = f"{uuid.uuid4().hex:s}"
        attribute_container = tasks.Task(session_identifier=session_identifier)

        self.assertIsNotNone(attribute_container.identifier)
        self.assertIsNotNone(attribute_container.start_time)
        self.assertIsNone(attribute_container.completion_time)

        expected_attribute_names = [
            "aborted",
            "completion_time",
            "file_entry_type",
            "has_retry",
            "identifier",
            "last_processing_time",
            "merge_priority",
            "number_of_retries",
            "path_spec",
            "session_identifier",
            "start_time",
            "storage_file_size",
            "storage_format",
        ]

        attribute_names = sorted(attribute_container.GetAttributeNames())

        self.assertEqual(attribute_names, expected_attribute_names)

    def testCreateRetryTask(self):
        """Tests the CreateRetryTask function."""
        session_identifier = f"{uuid.uuid4().hex:s}"
        task = tasks.Task(session_identifier=session_identifier)
        task.path_spec = "test_path_spec"

        retry_task = task.CreateRetryTask()
        self.assertNotEqual(retry_task.identifier, task.identifier)
        self.assertEqual(retry_task.number_of_retries, task.number_of_retries + 1)
        self.assertEqual(retry_task.path_spec, task.path_spec)

    def testUpdateProcessingTime(self):
        """Tests the UpdateProcessingTime function."""
        session_identifier = f"{uuid.uuid4().hex:s}"
        task = tasks.Task(session_identifier=session_identifier)

        self.assertIsNone(task.last_processing_time)

        task.UpdateProcessingTime()
        self.assertIsNotNone(task.last_processing_time)


if __name__ == "__main__":
    unittest.main()
