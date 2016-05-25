# -*- coding: utf-8 -*-
"""Error related attribute container object definitions."""

from plaso.containers import interface


# TODO: add AnalysisError.


class ExtractionError(interface.AttributeContainer):
  """Class to represent an extraction error attribute container.

  Attributes:
    message: a string containing the error message.
    parser_chain: a string containing the parser chain or None.
    path_spec: a path specification of the file entry (instance of
               dfvfs.PathSpec) or None.
  """
  CONTAINER_TYPE = u'extraction_error'

  def __init__(self, message, parser_chain=None, path_spec=None):
    """Initializes a parse error.

    Args:
      message: a string containing the error message.
      parser_chain: optional string containing the parser chain.
      path_spec: optional path specification of the file entry (instance of
                 dfvfs.PathSpec).
    """
    super(ExtractionError, self).__init__()
    self.message = message
    self.parser_chain = parser_chain
    self.path_spec = path_spec
