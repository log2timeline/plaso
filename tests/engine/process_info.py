#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests the class to get process information."""

import os
import unittest

from plaso.engine import process_info


class ProcessInfoTest(unittest.TestCase):
  """Tests the process information object."""

  def testInitialization(self):
    """Tests the initialization."""
    pid = os.getpid()
    process_information = process_info.ProcessInfo(pid)
    self.assertIsNotNone(process_information)

  def testGetUsedMemory(self):
    """Tests the GetUsedMemory function."""
    pid = os.getpid()
    process_information = process_info.ProcessInfo(pid)

    used_memory = process_information.GetUsedMemory()
    self.assertIsNotNone(used_memory)


if __name__ == '__main__':
  unittest.main()
