# -*- coding: utf-8 -*-
"""Operating system independent (generic) preprocessor plugins."""

from dfvfs.helpers import file_system_searcher

from plaso.lib import definitions
from plaso.preprocessors import interface
from plaso.preprocessors import manager


class DetermineOperatingSystemPlugin(
    interface.FileSystemArtifactPreprocessorPlugin):
  """Plugin to determine the operating system."""

  # pylint: disable=abstract-method
  # This plugin does not use an artifact definition and therefore does not
  # use _ParsePathSpecification.

  # We need to check for both forward and backward slashes since the path
  # specification will be dfVFS back-end dependent.
  _WINDOWS_LOCATIONS = set([
      '/windows/system32', '\\windows\\system32', '/winnt/system32',
      '\\winnt\\system32', '/winnt35/system32', '\\winnt35\\system32',
      '\\wtsrv\\system32', '/wtsrv/system32'])

  def __init__(self):
    """Initializes a plugin to determine the operating system."""
    super(DetermineOperatingSystemPlugin, self).__init__()
    self._find_specs = [
        file_system_searcher.FindSpec(
            case_sensitive=False, location='/etc',
            location_separator='/'),
        file_system_searcher.FindSpec(
            case_sensitive=False, location='/System/Library',
            location_separator='/'),
        file_system_searcher.FindSpec(
            case_sensitive=False, location='\\Windows\\System32',
            location_separator='\\'),
        file_system_searcher.FindSpec(
            case_sensitive=False, location='\\WINNT\\System32',
            location_separator='\\'),
        file_system_searcher.FindSpec(
            case_sensitive=False, location='\\WINNT35\\System32',
            location_separator='\\'),
        file_system_searcher.FindSpec(
            case_sensitive=False, location='\\WTSRV\\System32',
            location_separator='\\')]

  # pylint: disable=unused-argument
  def Collect(self, mediator, artifact_definition, searcher, file_system):
    """Collects values using a file artifact definition.

    Args:
      mediator (PreprocessMediator): mediates interactions between preprocess
          plugins and other components, such as storage and knowledge base.
      artifact_definition (artifacts.ArtifactDefinition): artifact definition.
      searcher (dfvfs.FileSystemSearcher): file system searcher to preprocess
          the file system.
      file_system (dfvfs.FileSystem): file system to be preprocessed.

    Raises:
      PreProcessFail: if the preprocessing fails.
    """
    locations = []
    for path_spec in searcher.Find(find_specs=self._find_specs):
      relative_path = searcher.GetRelativePath(path_spec)
      if relative_path:
        locations.append(relative_path.lower())

    operating_system = definitions.OPERATING_SYSTEM_FAMILY_UNKNOWN
    if self._WINDOWS_LOCATIONS.intersection(set(locations)):
      operating_system = definitions.OPERATING_SYSTEM_FAMILY_WINDOWS_NT

    elif '/system/library' in locations:
      operating_system = definitions.OPERATING_SYSTEM_FAMILY_MACOS

    elif '/etc' in locations:
      operating_system = definitions.OPERATING_SYSTEM_FAMILY_LINUX

    if operating_system != definitions.OPERATING_SYSTEM_FAMILY_UNKNOWN:
      mediator.SetValue('operating_system', operating_system)


manager.PreprocessPluginsManager.RegisterPlugins([
    DetermineOperatingSystemPlugin])
