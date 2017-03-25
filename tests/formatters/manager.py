#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the event formatters manager."""

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

    test_events = containers_test_lib.CreateTestEvents()
    for event in test_events:
      message, message_short = manager.FormattersManager.GetMessageStrings(
          formatter_mediator, event)
      source_short, source_long = manager.FormattersManager.GetSourceStrings(
          event)

      if source_short == u'LOG' and not text_message:
        text_message = message
        text_message_short = message_short

      csv_message_strings = u'{0:d},{1:s},{2:s},{3:s}'.format(
          event.timestamp, source_short, source_long, message)
      message_strings.append(csv_message_strings)

    self.assertIn((
        u'1334961526929596,REG,UNKNOWN,[MY AutoRun key] '
        u'Value: c:/Temp/evil.exe'), message_strings)

    self.assertIn(
        (u'1334966206929596,REG,UNKNOWN,'
         u'[HKEY_CURRENT_USER\\Secret\\EvilEmpire\\Malicious_key] '
         u'Value: send all the exes to the other world'), message_strings)
    self.assertIn(
        (u'1334940286000000,REG,UNKNOWN,'
         u'[HKEY_CURRENT_USER\\Windows\\Normal] '
         u'Value: run all the benign stuff'), message_strings)
    self.assertIn(
        (u'1335781787929596,FILE,Weird Log File,This log line reads '
         u'ohh so much.'), message_strings)
    self.assertIn(
        (u'1335781787929596,FILE,Weird Log File,Nothing of interest '
         u'here, move on.'), message_strings)
    self.assertIn(
        (u'1335791207939596,FILE,Weird Log File,Mr. Evil just logged '
         u'into the machine and got root.'), message_strings)

    expected_text_message = (
        u'This is a line by someone not reading the log line properly. And '
        u'since this log line exceeds the accepted 80 chars it will be '
        u'shortened.')
    self.assertEqual(text_message, expected_text_message)

    expected_text_message_short = (
        u'This is a line by someone not reading the log line properly. '
        u'And since this l...')
    self.assertEqual(text_message_short, expected_text_message_short)

    manager.FormattersManager.DeregisterFormatter(test_lib.TestEventFormatter)


if __name__ == '__main__':
  unittest.main()
