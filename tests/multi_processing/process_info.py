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
    process_information = process_info.ProcessInfo(pid)
    self.assertIsNotNone(process_information)

  def testProperties(self):
    """Tests the properties."""
    pid = os.getpid()
    process_information = process_info.ProcessInfo(pid)

    self.assertEqual(
        process_information.status, process_information.STATUS_RUNNING)

  def testGetMemoryInformation(self):
    """Tests the GetMemoryInformation function."""
    pid = os.getpid()
    process_information = process_info.ProcessInfo(pid)

    memory_information = process_information.GetMemoryInformation()
    self.assertIsNotNone(memory_information)


if __name__ == '__main__':
  unittest.main()
