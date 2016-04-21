# -*- coding: utf-8 -*-
"""Error related attribute container object definitions."""

from plaso.containers import interface


class ExtractionError(interface.AttributeContainer):
  """Class to represent an extraction error attribute container.

  Attributes:
    name: a string containing the parser or parser plugin name.
    description: a string containing the description of the error.
    file_path: optional string containing the path the parser that threw the
               error.
    level: optional integer containing the log level of the error.
    line_number: optional integer containing the code line that threw the
                 error.
    path_spec: optional path specification of the file entry (instance of
               dfvfs.PathSpec) or None.
  """
  def __init__(
      self, name, description, file_path=None, level=None, line_number=None,
      path_spec=None):
    """Initializes a parse error.

    Args:
      name: a string containing the parser or parser plugin name.
      description: a string containing the description of the error.
      file_path: optional string containing the path the parser that threw the
                 error.
      level: optional integer containing the log level of the error.
      line_number: optional integer containing the code line that threw the
                   error.
      path_spec: optional path specification of the file entry (instance of
                 dfvfs.PathSpec).
    """
    super(ExtractionError, self).__init__()
    self.description = description
    self.file_path = file_path
    self.level = level
    self.line_number = line_number
    self.name = name
    self.path_spec = path_spec
