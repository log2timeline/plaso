# -*- coding: utf-8 -*-
"""The analysis front-end."""

from plaso.frontend import frontend


class AnalysisFrontend(frontend.Frontend):
  """Class that implements an analysis front-end."""

  def __init__(self):
    """Initializes the front-end object."""
    super(AnalysisFrontend, self).__init__()
    self._data_location = None

  def SetDataLocation(self, data_location):
    """Set the data location.

    Args:
      data_location (str): path to the location that data files should
          be loaded from.
    """
    self._data_location = data_location
