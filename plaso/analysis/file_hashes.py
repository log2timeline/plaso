# -*- coding: utf-8 -*-
"""A plugin to generate a list of unique hashes and paths."""

from __future__ import unicode_literals

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.containers import reports


class FileHashesPlugin(interface.AnalysisPlugin):
  """A plugin for generating a list of file paths and corresponding hashes."""

  NAME = 'file_hashes'

  # Indicate that we can run this plugin during regular extraction.
  ENABLE_IN_EXTRACTION = True

  def __init__(self):
    """Initializes the unique hashes plugin."""
    super(FileHashesPlugin, self).__init__()
    self._paths_with_hashes = {}

  # pylint: disable=unused-argument
  def ExamineEvent(self, mediator, event, event_data):
    """Analyzes an event and creates extracts hashes as required.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.
      event (EventObject): event to examine.
      event_data (EventData): event data.
    """
    pathspec = getattr(event_data, 'pathspec', None)
    if pathspec is None:
      return

    if self._paths_with_hashes.get(pathspec, None):
      # We've already processed an event with this pathspec and extracted the
      # hashes from it.
      return

    hash_attributes = {}
    for attribute_name, attribute_value in event_data.GetAttributes():
      if attribute_name.endswith('_hash'):
        hash_attributes[attribute_name] = attribute_value
    self._paths_with_hashes[pathspec] = hash_attributes

  def _GeneratePathString(self, mediator, pathspec, hashes):
    """Generates a string containing a pathspec and its hashes.

    Args:
      mediator (AnalysisMediator): mediates interactions between analysis
          plugins and other components, such as storage and dfvfs.
      pathspec (dfvfs.Pathspec): the path specification) to generate a string
          for.
      hashes (dict[str, str]): mapping of hash attribute names to the value of
          that hash for the path specification being processed.

    Returns:
      str: string of the form "display_name: hash_type=hash_value". For example,
          "OS:/path/spec: test_hash=4 other_hash=5".
    """
    display_name = mediator.GetDisplayNameForPathSpec(pathspec)
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
    for pathspec, hashes in sorted(
        self._paths_with_hashes.items(),
        key=lambda tuple: tuple[0].comparable):

      path_string = self._GeneratePathString(mediator, pathspec, hashes)
      lines_of_text.append(path_string)

    lines_of_text.append('')
    report_text = '\n'.join(lines_of_text)
    return reports.AnalysisReport(plugin_name=self.NAME, text=report_text)


manager.AnalysisPluginManager.RegisterPlugin(FileHashesPlugin)
