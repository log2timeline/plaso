# -*- coding: utf-8 -*-
"""Front-end related functions and classes for testing."""

import io

from plaso.analysis import interface as analysis_interface


# TODO: replace by cli_test_lib.TestOutputWriter
class StringIOOutputWriter(object):
  """Class that implements a StringIO output writer."""

  def __init__(self):
    """Initialize the string output writer."""
    super(StringIOOutputWriter, self).__init__()
    self._string_io = io.StringIO()

    # Make the output writer compatible with a filehandle interface.
    self.write = self.Write

  def flush(self):
    """Flush the internal buffer."""
    self._string_io.flush()

  def GetValue(self):
    """Returns the write buffer from the output writer."""
    return self._string_io.getvalue()

  def GetLine(self):
    """Returns a single line read from the output buffer."""
    return self._string_io.readline()

  def SeekToBeginning(self):
    """Seeks the output buffer to the beginning of the buffer."""
    self._string_io.seek(0)

  def Write(self, string):
    """Writes a string to the StringIO object."""
    self._string_io.write(string)


class TestAnalysisPlugin(analysis_interface.AnalysisPlugin):
  """Test analysis plugin."""

  NAME = u'test_analysis_plugin'

  def CompileReport(self, unused_analysis_mediator):
    """Compiles a report of the analysis.

    After the plugin has received every copy of an event to
    analyze this function will be called so that the report
    can be assembled.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).

    Returns:
      The analysis report (instance of AnalysisReport).
    """
    return

  def ExamineEvent(
      self, unused_analysis_mediator, unused_event_object, **unused_kwargs):
    """Analyzes an event object.

    Args:
      analysis_mediator: The analysis mediator object (instance of
                         AnalysisMediator).
      event_object: An event object (instance of EventObject).
    """
    return
