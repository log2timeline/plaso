#!/usr/bin/python
# -*- coding: utf-8 -*-
"""This file contains a unit test for the event formatters."""

import unittest

from plaso.formatters import interface
from plaso.formatters import manager
from plaso.formatters import winreg  # pylint: disable=unused-import
from plaso.lib import event_test


class TestEvent1Formatter(interface.EventFormatter):
  """Test event 1 formatter."""
  DATA_TYPE = 'test:event1'
  FORMAT_STRING = u'{text}'

  SOURCE_SHORT = 'FILE'
  SOURCE_LONG = 'Weird Log File'


class WrongEventFormatter(interface.EventFormatter):
  """A simple event formatter."""
  DATA_TYPE = 'test:wrong'
  FORMAT_STRING = u'This format string does not match {body}.'

  SOURCE_SHORT = 'FILE'
  SOURCE_LONG = 'Weird Log File'


class FormattersManagerTest(unittest.TestCase):
  """Tests for the formatters manager."""

  def testFormatterRegistration(self):
    """Tests the RegisterFormatter and DeregisterFormatter functions."""
    # pylint: disable=protected-access
    number_of_formatters = len(manager.FormattersManager._formatter_classes)

    manager.FormattersManager.RegisterFormatter(TestEvent1Formatter)
    self.assertEquals(
        len(manager.FormattersManager._formatter_classes),
        number_of_formatters + 1)

    with self.assertRaises(KeyError):
      manager.FormattersManager.RegisterFormatter(TestEvent1Formatter)

    manager.FormattersManager.DeregisterFormatter(TestEvent1Formatter)
    self.assertEquals(
        len(manager.FormattersManager._formatter_classes),
        number_of_formatters)


class EventFormatterTest(unittest.TestCase):
  """Tests for the event formatter."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self._formatters_manager = manager.FormattersManager
    self.event_objects = event_test.GetEventObjects()

  def GetCSVLine(self, event_object):
    """Takes an EventObject and prints out a simple CSV line from it."""
    try:
      msg, _ = self._formatters_manager.GetMessageStrings(event_object)
      source_short, source_long = self._formatters_manager.GetSourceStrings(
          event_object)
    except KeyError:
      print event_object.GetAttributes()
    return u'{0:d},{1:s},{2:s},{3:s}'.format(
        event_object.timestamp, source_short, source_long, msg)

  def testInitialization(self):
    """Test the initialization."""
    self.assertTrue(TestEvent1Formatter())

  def testAttributes(self):
    """Test if we can read the event attributes correctly."""
    manager.FormattersManager.RegisterFormatter(TestEvent1Formatter)

    events = {}
    for event_object in self.event_objects:
      events[self.GetCSVLine(event_object)] = True

    self.assertIn((
        u'1334961526929596,REG,UNKNOWN key,[MY AutoRun key] Run: '
        u'c:/Temp/evil.exe'), events)

    self.assertIn(
        (u'1334966206929596,REG,UNKNOWN key,[//HKCU/Secret/EvilEmpire/'
         u'Malicious_key] Value: send all the exes to the other '
         u'world'), events)
    self.assertIn((u'1334940286000000,REG,UNKNOWN key,[//HKCU/Windows'
                   u'/Normal] Value: run all the benign stuff'), events)
    self.assertIn((u'1335781787929596,FILE,Weird Log File,This log line reads '
                   u'ohh so much.'), events)
    self.assertIn((u'1335781787929596,FILE,Weird Log File,Nothing of interest'
                   u' here, move on.'), events)
    self.assertIn((u'1335791207939596,FILE,Weird Log File,Mr. Evil just logged'
                   u' into the machine and got root.'), events)

    manager.FormattersManager.DeregisterFormatter(TestEvent1Formatter)

  def testTextBasedEvent(self):
    """Test a text based event."""
    for event_object in self.event_objects:
      source_short, _ = self._formatters_manager.GetSourceStrings(event_object)
      if source_short == 'LOG':
        msg, msg_short = self._formatters_manager.GetMessageStrings(
            event_object)

        self.assertEquals(msg, (
            u'This is a line by someone not reading the log line properly. And '
            u'since this log line exceeds the accepted 80 chars it will be '
            u'shortened.'))
        self.assertEquals(msg_short, (
            u'This is a line by someone not reading the log line properly. '
            u'And since this l...'))


class ConditionalTestEvent1(event_test.TestEvent1):
  DATA_TYPE = 'test:conditional_event1'


class ConditionalTestEvent1Formatter(interface.ConditionalEventFormatter):
  """Test event 1 conditional (event) formatter."""
  DATA_TYPE = 'test:conditional_event1'
  FORMAT_STRING_PIECES = [
      u'Description: {description}',
      u'Comment',
      u'Value: 0x{numeric:02x}',
      u'Optional: {optional}',
      u'Text: {text}']

  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Some Text File.'


class BrokenConditionalEventFormatter(interface.ConditionalEventFormatter):
  """A broken conditional event formatter."""
  DATA_TYPE = 'test:broken_conditional'
  FORMAT_STRING_PIECES = [u'{too} {many} formatting placeholders']

  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Some Text File.'


class ConditionalEventFormatterUnitTest(unittest.TestCase):
  """The unit test for the conditional event formatter."""

  def setUp(self):
    """Sets up the needed objects used throughout the test."""
    self.event_object = ConditionalTestEvent1(1335791207939596, {
        'numeric': 12, 'description': 'this is beyond words',
        'text': 'but we\'re still trying to say something about the event'})

  def testInitialization(self):
    """Test the initialization."""
    self.assertTrue(ConditionalTestEvent1Formatter())
    with self.assertRaises(RuntimeError):
      BrokenConditionalEventFormatter()

  def testGetMessages(self):
    """Test get messages."""
    event_formatter = ConditionalTestEvent1Formatter()
    msg, _ = event_formatter.GetMessages(self.event_object)

    expected_msg = (
        u'Description: this is beyond words Comment Value: 0x0c '
        u'Text: but we\'re still trying to say something about the event')
    self.assertEquals(msg, expected_msg)


if __name__ == '__main__':
  unittest.main()
