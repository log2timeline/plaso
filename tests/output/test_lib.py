# -*- coding: utf-8 -*-
"""Output related functions and classes for testing."""

import os
import unittest

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.path import factory as path_spec_factory

from plaso.containers import events
from plaso.formatters import interface as formatters_interface
from plaso.formatters import mediator as formatters_mediator
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import mediator


class TestConfig(object):
  """Test config value object."""


class TestEventObject(events.EventObject):
  """Test event object."""
  DATA_TYPE = u'test:output'

  def __init__(self):
    """Initialize the event object."""
    super(TestEventObject, self).__init__()
    self.timestamp = timelib.Timestamp.CopyFromString(u'2012-06-27 18:17:01')
    self.hostname = u'ubuntu'
    self.display_name = u'OS: /var/log/syslog.1'
    self.inode = 12345678
    self.text = (
        u'Reporter <CRON> PID: |8442| (pam_unix(cron:session): session\n '
        u'closed for user root)')
    self.username = u'root'
    self.uuid = u'79028cc28d324634a85533d0fbc49275'

    os_location = u'{0:s}{1:s}'.format(
        os.path.sep, os.path.join(u'cases', u'image.dd'))
    os_path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=os_location)
    self.pathspec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, inode=15,
        location=u'/var/log/syslog.1', parent=os_path_spec)


class TestEventFormatter(formatters_interface.EventFormatter):
  """Test event formatter."""
  DATA_TYPE = u'test:output'
  FORMAT_STRING = u'{text}'
  SOURCE_SHORT = u'LOG'
  SOURCE_LONG = u'Syslog'


class TestOutputModule(interface.LinearOutputModule):
  """This is a test output module that provides a simple XML."""

  NAME = u'test_xml'
  DESCRIPTION = u'Test output that provides a simple mocked XML.'

  def WriteEventBody(self, event_object):
    """Writes the body of an event object to the output.

    Args:
      event_object: the event object (instance of EventObject).
    """
    self._WriteLine((
        u'\t<Date>{0:s}</Date>\n\t<Time>{1:d}</Time>\n'
        u'\t<Entry>{2:s}</Entry>\n').format(
            event_object.date, event_object.timestamp, event_object.entry))

  def WriteEventEnd(self):
    """Writes the end of an event object to the output."""
    self._WriteLine(u'</Event>\n')

  def WriteEventStart(self):
    """Writes the start of an event object to the output."""
    self._WriteLine(u'<Event>\n')

  def WriteFooter(self):
    """Writes the footer to the output."""
    self._WriteLine(u'</EventFile>\n')

  def WriteHeader(self):
    """Writes the header to the output."""
    self._WriteLine(u'<EventFile>\n')


class OutputModuleTestCase(unittest.TestCase):
  """The unit test case for a output module."""

  # Show full diff results, part of TestCase so does not follow our naming
  # conventions.
  maxDiff = None

  def _CreateOutputMediator(self, storage_file=None):
    """Creates a test output mediator.

    Args:
      storage_file: optional storage file object (instance of StorageFile).

    Returns:
      An output mediator (instance of OutputMediator).
    """
    formatter_mediator = formatters_mediator.FormatterMediator()
    output_mediator = mediator.OutputMediator(formatter_mediator)

    if storage_file:
      output_mediator.SetStorageFile(storage_file)

    return output_mediator
