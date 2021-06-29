#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the logging related classes and functions."""

import logging
import os
import unittest

from plaso.lib import loggers

from tests import test_lib as shared_test_lib


class CompressedFileHandlerTests(shared_test_lib.BaseTestCase):
  """Tests for the compressed file handler for logging."""

  def testOpenAndEmit(self):
    """Tests the open and emit functions."""
    with shared_test_lib.TempDirectory() as temp_directory:
      filename = os.path.join(temp_directory, 'test.log.gz')
      handler = loggers.CompressedFileHandler(filename)

      record = logging.LogRecord(None, None, "", 0, "", (), None, None)
      handler.emit(record)


class LoggersTests(shared_test_lib.BaseTestCase):
  """Tests for the loggers module."""

  def testConfigureLogging(self):
    """Tests the ConfigureLogging function."""
    with shared_test_lib.TempDirectory() as temp_directory:
      filename = os.path.join(temp_directory, 'test.log.gz')
      loggers.ConfigureLogging(debug_output=True, filename=filename)

      filename = os.path.join(temp_directory, 'test.log')
      loggers.ConfigureLogging(filename=filename, quiet_mode=True)

    loggers.ConfigureLogging()


if __name__ == '__main__':
  unittest.main()
