# -*- coding: utf-8 -*-
"""Error related attribute container object definitions."""

from plaso.containers import interface


class ExtractionError(interface.AttributeContainer):
  """Class to represent an extraction error attribute container.

  Attributes:
    name: a string containing the parser or parser plugin name.
    description: a string containing the description of the error.
    path_spec: optional path specification of the file entry (instance of
               dfvfs.PathSpec) or None.
  """
  def __init__(self, name, description, path_spec=None):
    """Initializes a parse error.

    Args:
      name: a string containing the parser or parser plugin name.
      description: a string containing the description of the error.
      path_spec: optional path specification of the file entry (instance of
                 dfvfs.PathSpec).
    """
    super(ExtractionError, self).__init__()
    self.description = description
    self.name = name
    self.path_spec = path_spec
