#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the ips plugin interface."""

import abc

from plaso.parsers.ips_plugins import interface

from tests.parsers.ips_plugins import test_lib


class TestIPSPlugin(interface.IPSPlugin):
  """IPS plugin for test purposes."""

  NAME = 'test'
  DATA_FORMAT = 'ips test log'

  REQUIRED_HEADER_KEYS = ['app_name', 'app_version']
  REQUIRED_CONTENT_KEYS = ['procName', 'parentPid']

  def __int__(self):
    """Initializes"""
    super(TestIPSPlugin, self).__init__()

  # pylint: disable=arguments-differ
  @abc.abstractmethod
  def Process(self, parser_mediator, ips_file=None, **unused_kwargs):
    """Extracts information from an ips log file.

    This is the main method that an ips plugin needs to implement.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      ips_file (Optional[IPSFile]): database.

    Raises:
      ValueError: If the file value is missing.
    """


class IPSInterfaceTest(test_lib.IPSPluginTestCase):
  """Tests for the ips plugin interface"""

  def testCheckRequiredKeys(self):
    """Tests the CheckRequiredKeys function."""
    plugin = TestIPSPlugin()

    _, ips_file = self._OpenIPSFile(['ips', 'application_crash_log.ips'])

    required_key_present = plugin.CheckRequiredKeys(ips_file)
    self.assertTrue(required_key_present)
