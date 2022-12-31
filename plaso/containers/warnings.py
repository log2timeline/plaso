# -*- coding: utf-8 -*-
"""Warning attribute containers."""

from acstore.containers import interface
from acstore.containers import manager


class AnalysisWarning(interface.AttributeContainer):
  """Analysis warning attribute container.

  Analysis warnings are produced by analysis plugins when they encounter
  situations that should be brought to the users' attention but are not
  analysis results.

  Attributes:
    message (str): warning message.
    plugin_name (str): name of the analysis plugin to which the warning applies.
  """
  CONTAINER_TYPE = 'analysis_warning'

  SCHEMA = {
      'message': 'str',
      'plugin_name': 'str'}

  def __init__(self, message=None, plugin_name=None):
    """Initializes an analysis warning.

    Args:
      message (Optional[str]): warning message.
      plugin_name (Optional[str]): name of the analysis plugin to which the
          warning applies.
    """
    super(AnalysisWarning, self).__init__()
    self.message = message
    self.plugin_name = plugin_name


class ExtractionWarning(interface.AttributeContainer):
  """Extraction warning attribute container.

  Extraction warnings are produced by parsers/plugins when they encounter
  situations that should be brought to the users' attention but are not
  event data derived from the data being processed.

  Attributes:
    message (str): warning message.
    parser_chain (str): parser chain to which the warning applies.
    path_spec (dfvfs.PathSpec): path specification of the file entry to which
        the warning applies.
  """
  CONTAINER_TYPE = 'extraction_warning'

  SCHEMA = {
      'message': 'str',
      'parser_chain': 'str',
      'path_spec': 'dfvfs.PathSpec'}

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


class PreprocessingWarning(interface.AttributeContainer):
  """Preprocessing warning attribute container.

  Preprocessing warnings are produced by preprocessing plugins when they
  encounter situations that should be brought to the users' attention but are
  not preprocessing results.

  Attributes:
    message (str): warning message.
    path_spec (dfvfs.PathSpec): path specification of the file entry to which
        the warning applies.
    plugin_name (str): name of the preprocessing plugin to which the warning
        applies.
  """
  CONTAINER_TYPE = 'preprocessing_warning'

  SCHEMA = {
      'message': 'str',
      'path_spec': 'dfvfs.PathSpec',
      'plugin_name': 'str'}

  def __init__(self, message=None, path_spec=None, plugin_name=None):
    """Initializes an extraction warning.

    Args:
      message (Optional[str]): warning message.
      path_spec (Optional[dfvfs.PathSpec]): path specification of the file entry
          to which the warning applies.
      plugin_name (Optional[str]): name of the preprocessing plugin to which the
          warning applies.
    """
    super(PreprocessingWarning, self).__init__()
    self.message = message
    self.path_spec = path_spec
    self.plugin_name = plugin_name


class RecoveryWarning(interface.AttributeContainer):
  """Recovery warning attribute container.

  Recovery warnings are warning encountered during recovery. They are typically
  produced by parsers/plugins when they are unable to recover event data.

  Attributes:
    message (str): warning message.
    parser_chain (str): parser chain to which the warning applies.
    path_spec (dfvfs.PathSpec): path specification of the file entry to which
        the warning applies.
  """
  CONTAINER_TYPE = 'recovery_warning'

  SCHEMA = {
      'message': 'str',
      'parser_chain': 'str',
      'path_spec': 'dfvfs.PathSpec'}

  def __init__(self, message=None, parser_chain=None, path_spec=None):
    """Initializes a recovery warning.

    Args:
      message (Optional[str]): warning message.
      parser_chain (Optional[str]): parser chain to which the warning applies.
      path_spec (Optional[dfvfs.PathSpec]): path specification of the file entry
          to which the warning applies.
    """
    super(RecoveryWarning, self).__init__()
    self.message = message
    self.parser_chain = parser_chain
    self.path_spec = path_spec


class TimeliningWarning(interface.AttributeContainer):
  """Timelining warning attribute container.

  Timelining warnings are produced by the timeliner when it encounters
  situations that should be brought to the users' attention but are not
  events derived from the event data being processed.

  Attributes:
    message (str): warning message.
    parser_chain (str): parser chain to which the warning applies.
    path_spec (dfvfs.PathSpec): path specification of the file entry to which
        the warning applies.
  """
  CONTAINER_TYPE = 'timelining_warning'

  SCHEMA = {
      'message': 'str',
      'parser_chain': 'str',
      'path_spec': 'dfvfs.PathSpec'}

  def __init__(self, message=None, parser_chain=None, path_spec=None):
    """Initializes a timelining warning.

    Args:
      message (Optional[str]): warning message.
      parser_chain (Optional[str]): parser chain to which the warning applies.
      path_spec (Optional[dfvfs.PathSpec]): path specification of the file entry
          to which the warning applies.
    """
    super(TimeliningWarning, self).__init__()
    self.message = message
    self.parser_chain = parser_chain
    self.path_spec = path_spec


manager.AttributeContainersManager.RegisterAttributeContainers([
    AnalysisWarning, ExtractionWarning, PreprocessingWarning, RecoveryWarning,
    TimeliningWarning])
