# -*- coding: utf-8 -*-
"""Error attribute containers."""

from plaso.containers import interface
from plaso.containers import manager


# TODO: add AnalysisError.


class ExtractionError(interface.AttributeContainer):
  """Extraction error attribute container.

  Attributes:
    message (str): error message.
    parser_chain (str): parser chain to which the error applies.
    path_spec (dfvfs.PathSpec):
        path specification of the file entry to which the error applies.
  """
  CONTAINER_TYPE = u'extraction_error'

  def __init__(self, message=None, parser_chain=None, path_spec=None):
    """Initializes a parse error.

    Args:
      message (Optional[str]): error message.
      parser_chain (Optional[str]): parser chain to which the error applies.
      path_spec (Optional[dfvfs.PathSpec]):
          path specification of the file entry to which the error applies.
    """
    super(ExtractionError, self).__init__()
    self.message = message
    self.parser_chain = parser_chain
    self.path_spec = path_spec


manager.AttributeContainersManager.RegisterAttributeContainer(ExtractionError)
