# -*- coding: utf-8 -*-
"""A plugin to generate a list of unique hashes and paths."""

from plaso.analysis import interface
from plaso.analysis import manager


class FileHashesPlugin(interface.AnalysisPlugin):
  """A plugin for generating a list of file paths and corresponding hashes."""

  NAME = 'file_hashes'

  def __init__(self):
    """Initializes the unique hashes plugin."""
    super(FileHashesPlugin, self).__init__()
    self._paths_with_hashes = {}

  # pylint: disable=unused-argument
  def ExamineEvent(self, mediator, event, event_data, event_data_stream):
    """Analyzes an event and creates extracts hashes as required.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.
      event (EventObject): event to examine.
      event_data (EventData): event data.
      event_data_stream (EventDataStream): event data stream.
    """
    path_specification = getattr(event_data_stream, 'path_spec', None)
    if not path_specification:
      # Note that support for event_data.pathspec is kept for backwards
      # compatibility.
      path_specification = getattr(event_data, 'pathspec', None)

    if not path_specification:
      return

    if self._paths_with_hashes.get(path_specification, None):
      # We've already processed an event with this path specification and
      # extracted the hashes from it.
      return

    hash_attributes_container = event_data_stream
    if not hash_attributes_container:
      hash_attributes_container = event_data

    hash_attributes = {}
    for attribute_name, attribute_value in (
        hash_attributes_container.GetAttributes()):
      if attribute_name.endswith('_hash'):
        hash_attributes[attribute_name] = attribute_value
    self._paths_with_hashes[path_specification] = hash_attributes

  def _GeneratePathString(self, mediator, path_spec, hashes):
    """Generates a string containing a path specification and its hashes.

    Args:
      mediator (AnalysisMediator): mediates interactions between analysis
          plugins and other components, such as storage and dfvfs.
      path_spec (dfvfs.Pathspec): the path specification) to generate a string
          for.
      hashes (dict[str, str]): mapping of hash attribute names to the value of
          that hash for the path specification being processed.

    Returns:
      str: string of the form "display_name: hash_type=hash_value". For example,
          "OS:/path/spec: test_hash=4 other_hash=5".
    """
    display_name = mediator.GetDisplayNameForPathSpec(path_spec)
    path_string = '{0:s}:'.format(display_name)
    for hash_name, hash_value in sorted(hashes.items()):
      path_string = '{0:s} {1:s}={2:s}'.format(
          path_string, hash_name, hash_value)
    return path_string

  def CompileReport(self, mediator):
    """Compiles an analysis report.

    Args:
      mediator (AnalysisMediator): mediates interactions between analysis
          plugins and other components, such as storage and dfvfs.

    Returns:
      AnalysisReport: report.
    """
    lines_of_text = ['Listing file paths and hashes']
    for path_spec, hashes in sorted(
        self._paths_with_hashes.items(),
        key=lambda tuple: tuple[0].comparable):

      path_string = self._GeneratePathString(mediator, path_spec, hashes)
      lines_of_text.append(path_string)

    lines_of_text.append('')
    report_text = '\n'.join(lines_of_text)
    analysis_report = super(FileHashesPlugin, self).CompileReport(mediator)
    analysis_report.text = report_text
    return analysis_report


manager.AnalysisPluginManager.RegisterPlugin(FileHashesPlugin)
