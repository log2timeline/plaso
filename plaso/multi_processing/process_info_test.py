#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the class to get process information."""

import os
import unittest

from plaso.multi_processing import process_info


class ProcessInfoTest(unittest.TestCase):
  """Tests the process information object."""

  def testInitialization(self):
    """Tests the initialization."""
    pid = os.getpid()
    process_info_object = process_info.ProcessInfo(pid)
    self.assertNotEqual(process_info_object, None)

  def testProperties(self):
    """Tests the properties."""
    pid = os.getpid()
    process_info_object = process_info.ProcessInfo(pid)

    self.assertEqual(process_info_object.pid, pid)

    self.assertEqual(
        process_info_object.status, process_info_object.STATUS_RUNNING)

    # The following values will vary per platform and how the test is invoked.
    self.assertNotEqual(process_info_object.command_line, None)
    self.assertNotEqual(process_info_object.cpu_percent, None)
    self.assertNotEqual(process_info_object.cpu_times, None)
    self.assertNotEqual(process_info_object.io_counters, None)
    self.assertNotEqual(process_info_object.memory_map, None)
    self.assertNotEqual(process_info_object.name, None)
    self.assertNotEqual(process_info_object.number_of_threads, 0)
    self.assertNotEqual(process_info_object.open_files, None)
    self.assertNotEqual(process_info_object.parent, None)
    self.assertNotEqual(process_info_object.start_time, None)

    for _ in process_info_object.children:
      pass

  def testIsAlive(self):
    """Tests the IsAlive function."""
    pid = os.getpid()
    process_info_object = process_info.ProcessInfo(pid)

    self.assertTrue(process_info_object.IsAlive())

  def testGetMemoryInformation(self):
    """Tests the GetMemoryInformation function."""
    pid = os.getpid()
    process_info_object = process_info.ProcessInfo(pid)

    memory_information = process_info_object.GetMemoryInformation()
    self.assertNotEqual(memory_information, None)

  # TODO: add test for TerminateProcess()?


if __name__ == '__main__':
  unittest.main()
