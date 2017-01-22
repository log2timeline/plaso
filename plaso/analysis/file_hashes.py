# -*- coding: utf-8 -*-
"""A plugin to generate a list of unique hashes and paths."""

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.containers import reports


class FileHashesPlugin(interface.AnalysisPlugin):
  """A plugin for generating a list of file paths and corresponding hashes."""

  NAME = u'file_hashes'

  # Indicate that we can run this plugin during regular extraction.
  ENABLE_IN_EXTRACTION = True

  def __init__(self):
    """Initializes the unique hashes plugin."""
    super(FileHashesPlugin, self).__init__()
    self._paths_with_hashes = {}

  def ExamineEvent(self, mediator, event):
    """Analyzes an event and creates extracts hashes as required.

    Args:
      mediator (AnalysisMediator): mediates interactions between
          analysis plugins and other components, such as storage and dfvfs.
      event (EventObject): event to examine.
    """
    path_specification = getattr(event, u'pathspec', None)
    if path_specification is None:
      return

    if self._paths_with_hashes.get(path_specification, None):
      # We've already processed an event with this path_specification and
      # extracted the hashes from it.
      return

    hash_attributes = {}
    for attribute_name, attribute_value in event.GetAttributes():
      if attribute_name.endswith(u'_hash'):
        hash_attributes[attribute_name] = attribute_value

    self._paths_with_hashes[path_specification] = hash_attributes

  def _GeneratePathString(self, mediator, path_specification, hashes):
    """Generates a string containing a path specification and its hashes.

    Args:
      mediator (AnalysisMediator): mediates interactions between analysis
          plugins and other components, such as storage and dfvfs.
      path_specification (dfvfs.Pathspec): the path specification to generate
          a string for.
      hashes (dict[str, str]): mapping of hash attribute names to the value of
          that hash for the path specification being processed.

    Returns:
      str: string of the form "display_name: hash_type=hash_value". For example,
          "OS:/path/spec: test_hash=4 other_hash=5".
    """
    display_name = mediator.GetDisplayName(path_specification)
    path_string = u'{0:s}:'.format(display_name)
    for hash_name, hash_value in sorted(hashes.items()):
      path_string = u'{0:s} {1:s}={2:s}'.format(
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
    lines_of_text = [u'Listing file paths and hashes']
    for path_specification, hashes in sorted(
        self._paths_with_hashes.items(),
        key=lambda tuple: tuple[0].comparable):

      path_string = self._GeneratePathString(
          mediator, path_specification, hashes)
      lines_of_text.append(path_string)

    lines_of_text.append(u'')
    report_text = u'\n'.join(lines_of_text)
    return reports.AnalysisReport(plugin_name=self.NAME, text=report_text)


manager.AnalysisPluginManager.RegisterPlugin(FileHashesPlugin)
