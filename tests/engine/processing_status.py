#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests the processing status."""

import unittest

from plaso.engine import processing_status


class ProcessStatusTest(unittest.TestCase):
  """Tests the process status."""

  def testUpdateNumberOfEventReports(self):
    """Tests the UpdateNumberOfEventReports function."""
    process_status = processing_status.ProcessStatus()

    process_status.UpdateNumberOfEventReports(5, 5)

    with self.assertRaises(ValueError):
      process_status.UpdateNumberOfEventReports(1, 10)

    with self.assertRaises(ValueError):
      process_status.UpdateNumberOfEventReports(10, 1)

  def testUpdateNumberOfEvents(self):
    """Tests the UpdateNumberOfEvents function."""
    process_status = processing_status.ProcessStatus()

    process_status.UpdateNumberOfEvents(5, 5)

    with self.assertRaises(ValueError):
      process_status.UpdateNumberOfEvents(1, 10)

    with self.assertRaises(ValueError):
      process_status.UpdateNumberOfEvents(10, 1)

  def testUpdateNumberOfEventSources(self):
    """Tests the UpdateNumberOfEventSources function."""
    process_status = processing_status.ProcessStatus()

    process_status.UpdateNumberOfEventSources(5, 5)

    with self.assertRaises(ValueError):
      process_status.UpdateNumberOfEventSources(1, 10)

    with self.assertRaises(ValueError):
      process_status.UpdateNumberOfEventSources(10, 1)

  def testUpdateNumberOfEventTags(self):
    """Tests the UpdateNumberOfEventTags function."""
    process_status = processing_status.ProcessStatus()

    process_status.UpdateNumberOfEventTags(5, 5)

    with self.assertRaises(ValueError):
      process_status.UpdateNumberOfEventTags(1, 10)

    with self.assertRaises(ValueError):
      process_status.UpdateNumberOfEventTags(10, 1)


class ProcessingStatusTest(unittest.TestCase):
  """Tests the processing status."""

  # pylint: disable=protected-access

  def testWorkersStatus(self):
    """Tests the workers_status property."""
    status = processing_status.ProcessingStatus()
    self.assertEqual(status.workers_status, [])

  def testUpdateProcessStatus(self):
    """Tests the _UpdateProcessStatus function."""
    process_status = processing_status.ProcessStatus()

    status = processing_status.ProcessingStatus()
    status._UpdateProcessStatus(
        process_status, 'test', 'Idle', 12345, 2000000, 'test process',
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

  def testUpdateForemanStatus(self):
    """Tests the UpdateForemanStatus function."""
    status = processing_status.ProcessingStatus()
    status.UpdateForemanStatus(
        'test', 'Idle', 12345, 2000000, 'test process',
        0, 0, 0, 0, 0, 0, 0, 0, 0, 0)

  def testUpdateTasksStatus(self):
    """Tests the UpdateTasksStatus function."""
    task_status = processing_status.TasksStatus()

    status = processing_status.ProcessingStatus()
    status.UpdateTasksStatus(task_status)

  def testUpdateWorkerStatus(self):
    """Tests the UpdateWorkerStatus function."""
    status = processing_status.ProcessingStatus()
    status.UpdateWorkerStatus(
        'test', 'Idle', 12345, 2000000, 'test process', 0,
        0, 0, 0, 0, 0, 0, 0, 0, 0)


class TasksStatusTest(unittest.TestCase):
  """Tests the task status."""

  def testInitialization(self):
    """Tests the __init__ function."""
    task_status = processing_status.TasksStatus()
    self.assertIsNotNone(task_status)


if __name__ == '__main__':
  unittest.main()
