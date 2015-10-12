#!/usr/bin/python
# -*- coding: utf-8 -*-
"""Tests for the event formatters manager."""

import unittest

from plaso.formatters import manager
from plaso.formatters import mediator
from plaso.formatters import winreg  # pylint: disable=unused-import

from tests.lib import event as event_test_lib
from tests.formatters import test_lib


class FormattersManagerTest(unittest.TestCase):
  """Tests for the event formatters manager."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._event_objects = event_test_lib.GetEventObjects()

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
    for event_object in self._event_objects:
      message, message_short = manager.FormattersManager.GetMessageStrings(
          formatter_mediator, event_object)
      source_short, source_long = manager.FormattersManager.GetSourceStrings(
          event_object)

      if source_short == u'LOG' and not text_message:
        text_message = message
        text_message_short = message_short

      csv_message_strings = u'{0:d},{1:s},{2:s},{3:s}'.format(
          event_object.timestamp, source_short, source_long, message)
      message_strings.append(csv_message_strings)

    self.assertIn((
        u'1334961526929596,REG,UNKNOWN,[MY AutoRun key] Run: '
        u'c:/Temp/evil.exe'), message_strings)

    self.assertIn(
        (u'1334966206929596,REG,UNKNOWN,[//HKCU/Secret/EvilEmpire/'
         u'Malicious_key] Value: send all the exes to the other '
         u'world'), message_strings)
    self.assertIn(
        (u'1334940286000000,REG,UNKNOWN,[//HKCU/Windows'
         u'/Normal] Value: run all the benign stuff'), message_strings)
    self.assertIn(
        (u'1335781787929596,FILE,Weird Log File,This log line reads '
         u'ohh so much.'), message_strings)
    self.assertIn(
        (u'1335781787929596,FILE,Weird Log File,Nothing of interest'
         u' here, move on.'), message_strings)
    self.assertIn(
        (u'1335791207939596,FILE,Weird Log File,Mr. Evil just logged'
         u' into the machine and got root.'), message_strings)

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
