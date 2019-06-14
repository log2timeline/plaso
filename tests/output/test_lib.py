# -*- coding: utf-8 -*-
"""Output related functions and classes for testing."""

from __future__ import unicode_literals

from plaso.engine import knowledge_base
from plaso.formatters import interface as formatters_interface
from plaso.formatters import mediator as formatters_mediator
from plaso.lib import timelib
from plaso.output import interface
from plaso.output import mediator

from tests import test_lib as shared_test_lib


class TestConfig(object):
  """Test configuration."""


class TestEventFormatter(formatters_interface.EventFormatter):
  """Test event formatter."""
  DATA_TYPE = 'test:output'
  FORMAT_STRING = '{text}'
  SOURCE_SHORT = 'LOG'
  SOURCE_LONG = 'Syslog'


class TestOutputModule(interface.LinearOutputModule):
  """This is a test output module that provides a simple XML."""

  NAME = 'test_xml'
  DESCRIPTION = 'Test output that provides a simple mocked XML.'

  def WriteEventBody(self, event, event_data, event_tag):
    """Writes the body of an event to the output.

    Args:
      event (EventObject): event.
      event_data (EventData): event data.
      event_tag (EventTag): event tag.
    """
    date_time = timelib.Timestamp.CopyToIsoFormat(
        event.timestamp, timezone=self._output_mediator.timezone,
        raise_error=False)

    output_text = (
        '\t<DateTime>{0:s}</DateTime>\n'
        '\t<Entry>{1:s}</Entry>\n').format(date_time, event_data.entry)
    self._output_writer.Write(output_text)

    # TODO: add support for event tag.

  def WriteEventEnd(self):
    """Writes the end of an event to the output."""
    self._output_writer.Write('</Event>\n')

  def WriteEventStart(self):
    """Writes the start of an event to the output."""
    self._output_writer.Write('<Event>\n')

  def WriteFooter(self):
    """Writes the footer to the output."""
    self._output_writer.Write('</EventFile>\n')

  def WriteHeader(self):
    """Writes the header to the output."""
    self._output_writer.Write('<EventFile>\n')


class OutputModuleTestCase(shared_test_lib.BaseTestCase):
  """The unit test case for a output module."""

  def _CreateOutputMediator(self, storage_file=None):
    """Creates a test output mediator.

    Args:
      storage_file (Optional[StorageFile]): storage file.

    Returns:
      OutputMediator: output mediator.
    """
    knowledge_base_object = knowledge_base.KnowledgeBase()

    if storage_file:
      storage_file.ReadPreprocessingInformation(knowledge_base_object)

    formatter_mediator = formatters_mediator.FormatterMediator()
    output_mediator = mediator.OutputMediator(
        knowledge_base_object, formatter_mediator)

    return output_mediator
