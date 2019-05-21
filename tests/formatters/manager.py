#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the event formatters manager."""

from __future__ import unicode_literals

import unittest

from plaso.formatters import manager
from plaso.formatters import mediator
from plaso.formatters import winreg  # pylint: disable=unused-import

from tests import test_lib as shared_test_lib
from tests.containers import test_lib as containers_test_lib
from tests.formatters import test_lib


class FormattersManagerTest(shared_test_lib.BaseTestCase):
  """Tests for the event formatters manager."""

  def testFormatterRegistration(self):
    """Tests the RegisterFormatter and DeregisterFormatter functions."""
    # pylint: disable=protected-access
    number_of_formatters = len(manager.FormattersManager._formatter_classes)

    manager.FormattersManager.RegisterFormatter(test_lib.TestEventFormatter)
    self.assertEqual(
        len(manager.FormattersManager._formatter_classes),
        number_of_formatters + 1)

    with self.assertRaises(KeyError):
      manager.FormattersManager.RegisterFormatter(test_lib.TestEventFormatter)

    manager.FormattersManager.DeregisterFormatter(test_lib.TestEventFormatter)
    self.assertEqual(
        len(manager.FormattersManager._formatter_classes),
        number_of_formatters)

  def testMessageStrings(self):
    """Tests the GetMessageStrings and GetSourceStrings functions."""
    manager.FormattersManager.RegisterFormatter(test_lib.TestEventFormatter)

    formatter_mediator = mediator.FormatterMediator()

    message_strings = []
    text_message = None
    text_message_short = None

    for event, event_data in containers_test_lib.CreateTestEvents():
      message, message_short = manager.FormattersManager.GetMessageStrings(
          formatter_mediator, event_data)
      source_short, source_long = manager.FormattersManager.GetSourceStrings(
          event, event_data)

      if source_short == 'LOG' and not text_message:
        text_message = message
        text_message_short = message_short

      csv_message_strings = '{0:d},{1:s},{2:s},{3:s}'.format(
          event.timestamp, source_short, source_long, message)
      message_strings.append(csv_message_strings)

    self.assertIn((
        '1334961526929596,REG,UNKNOWN,[MY AutoRun key] '
        'Value: c:/Temp/evil.exe'), message_strings)

    self.assertIn((
        '1334966206929596,REG,UNKNOWN,'
        '[HKEY_CURRENT_USER\\Secret\\EvilEmpire\\Malicious_key] '
        'Value: send all the exes to the other world'), message_strings)
    self.assertIn((
        '1334940286000000,REG,UNKNOWN,'
        '[HKEY_CURRENT_USER\\Windows\\Normal] '
        'Value: run all the benign stuff'), message_strings)
    self.assertIn((
        '1335781787929596,FILE,Weird Log File,This log line reads '
        'ohh so much.'), message_strings)
    self.assertIn((
        '1335781787929596,FILE,Weird Log File,Nothing of interest '
        'here, move on.'), message_strings)
    self.assertIn((
        '1335791207939596,FILE,Weird Log File,Mr. Evil just logged '
        'into the machine and got root.'), message_strings)

    expected_text_message = (
        'This is a line by someone not reading the log line properly. And '
        'since this log line exceeds the accepted 80 chars it will be '
        'shortened.')
    self.assertEqual(text_message, expected_text_message)

    expected_text_message_short = (
        'This is a line by someone not reading the log line properly. '
        'And since this l...')
    self.assertEqual(text_message_short, expected_text_message_short)

    manager.FormattersManager.DeregisterFormatter(test_lib.TestEventFormatter)


if __name__ == '__main__':
  unittest.main()
