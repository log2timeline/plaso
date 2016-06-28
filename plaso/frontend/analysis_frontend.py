# -*- coding: utf-8 -*-
"""The analysis front-end."""

from plaso.formatters import mediator as formatters_mediator
from plaso.frontend import frontend


class AnalysisFrontend(frontend.Frontend):
  """Class that implements an analysis front-end."""

  def __init__(self):
    """Initializes the front-end object."""
    super(AnalysisFrontend, self).__init__()
    self._data_location = None

  def GetFormatterMediator(self):
    """Retrieves the formatter mediator.

    Returns:
      The formatter mediator (instance of FormatterMediator).
    """
    return formatters_mediator.FormatterMediator(
        data_location=self._data_location)

  def SetDataLocation(self, data_location):
    """Set the data location.

    Args:
      data_location: The path to the location that data files should be loaded
                     from.
    """
    self._data_location = data_location
