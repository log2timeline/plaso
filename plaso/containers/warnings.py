# -*- coding: utf-8 -*-
"""Warning attribute containers."""

from __future__ import unicode_literals

from plaso.containers import interface
from plaso.containers import manager


# TODO: add AnalysisWarning.


class ExtractionWarning(interface.AttributeContainer):
  """Extraction warning attribute container.

  Extraction warnings are produced by parsers/plugins as well the Plaso engine
  when they encounter situations that should be brought to the users' attention
  but are not events derived from the data being processed.

  Attributes:
    message (str): warning message.
    parser_chain (str): parser chain to which the warning applies.
    path_spec (dfvfs.PathSpec): path specification of the file entry to which
        the warning applies.
  """
  CONTAINER_TYPE = 'extraction_warning'

  def __init__(self, message=None, parser_chain=None, path_spec=None):
    """Initializes an extraction warning.

    Args:
      message (Optional[str]): warning message.
      parser_chain (Optional[str]): parser chain to which the warning applies.
      path_spec (Optional[dfvfs.PathSpec]): path specification of the file entry
          to which the warning applies.
    """
    super(ExtractionWarning, self).__init__()
    self.message = message
    self.parser_chain = parser_chain
    self.path_spec = path_spec


class ExtractionError(ExtractionWarning):
  """Extraction error attribute container.

  This class is provided for backwards compatiblity only, all new code must use
  ExtractionWarning.

  Attributes:
    message (str): warning message.
    parser_chain (str): parser chain to which the warning applies.
    path_spec (dfvfs.PathSpec): path specification of the file entry to which
        the warning applies.
  """
  CONTAINER_TYPE = 'extraction_error'


manager.AttributeContainersManager.RegisterAttributeContainers(
    [ExtractionError, ExtractionWarning])
