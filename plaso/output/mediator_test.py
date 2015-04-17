#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the output mediator object."""

import unittest

from plaso.output import mediator
from plaso.output import test_lib


class OutputMediatorTest(unittest.TestCase):
  """Tests for the output mediator object."""

  def testInitialization(self):
    """Tests the initialization."""
    output_mediator = mediator.OutputMediator(None, None)
    self.assertNotEqual(output_mediator, None)

  def testGetConfigurationValue(self):
    """Tests the GetConfigurationValue function."""
    expected_config_value = u'My test config setting.'

    config = test_lib.TestConfig()
    config.my_setting = expected_config_value

    output_mediator = mediator.OutputMediator(None, None, config=config)
    self.assertNotEqual(output_mediator, None)

    config_value = output_mediator.GetConfigurationValue(u'my_setting')
    self.assertEqual(config_value, expected_config_value)

    config_value = output_mediator.GetConfigurationValue(u'bogus')
    self.assertEqual(config_value, None)

  # TODO: add more tests:
  # GetEventFormatter test.
  # GetFormattedMessages test.
  # GetFormattedSources test.
  # GetFormatStringAttributeNames test.
  # GetHostname test.
  # GetMACBRepresentation test.
  # GetStoredHostname test.
  # GetUsername test.


if __name__ == '__main__':
  unittest.main()
