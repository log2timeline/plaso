#!/usr/bin/env python3
"""Tests the process information."""

import os
import unittest

from plaso.engine import process_info


class ProcessInfoTest(unittest.TestCase):
  """Tests the process information."""

  def testInitialization(self):
    """Tests the __init__ function."""
    pid = os.getpid()
    process_information = process_info.ProcessInfo(pid)
    self.assertIsNotNone(process_information)

    with self.assertRaises(OSError):
      process_info.ProcessInfo(-1)

  def testGetUsedMemory(self):
    """Tests the GetUsedMemory function."""
    pid = os.getpid()
    process_information = process_info.ProcessInfo(pid)

    used_memory = process_information.GetUsedMemory()
    self.assertIsNotNone(used_memory)


if __name__ == '__main__':
  unittest.main()
