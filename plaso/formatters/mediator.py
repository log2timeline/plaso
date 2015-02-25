# -*- coding: utf-8 -*-
"""The formatter mediator object."""


class FormatterMediator(object):
  """Class that implements the formatter mediator."""

  def __init__(self, data_location=None):
    """Initializes a formatter mediator object.

    Args:
      data_location: the path of the formatter data files.
                     The default is None.
    """
    super(FormatterMediator, self).__init__()
    self._data_location = data_location
