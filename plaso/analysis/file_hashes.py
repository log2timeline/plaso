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

  def __init__(self, incoming_queue):
    """Initializes the unique hashes plugin.

    Args:
      incoming_queue: a queue to read events from.
    """
    super(FileHashesPlugin, self).__init__(incoming_queue)
    self._paths_with_hashes = {}

  def ExamineEvent(self, analysis_mediator, event_object, **kwargs):
    """Analyzes an event_object and creates extracts hashes as required.

    Args:
      analysis_mediator: the analysis mediator object (instance of
                         AnalysisMediator).
      event_object: the event object (instance of EventObject) to examine.
    """
    pathspec = getattr(event_object, u'pathspec', None)
    if pathspec is None:
      return
    if self._paths_with_hashes.get(pathspec, None):
      # We've already processed an event with this pathspec and extracted the
      # hashes from it.
      return
    hash_attributes = {}
    for attribute_name, attribute_value in event_object.GetAttributes():
      if attribute_name.endswith(u'_hash'):
        hash_attributes[attribute_name] = attribute_value
    self._paths_with_hashes[pathspec] = hash_attributes

  def _GeneratePathString(self, analysis_mediator, pathspec, hashes):
    """Generates a string containing a pathspec and its hashes.

    Args:
      analysis_mediator: the analysis mediator object (instance of
                         AnalysisMediator).
      pathspec: the path specification (instance of dfVFS.PathSpec) to
                generate a string for.
      hashes: a dictionary mapping hash attribute names to the value of
              that hash for the path specification being processed.

    Returns:
      A string of the form "OS:/path/spec: test_hash=4".
    """
    display_name = analysis_mediator.GetDisplayName(pathspec)
    path_string = u'{0:s}:'.format(display_name)
    for hash_name, hash_value in sorted(hashes.items()):
      path_string = u'{0:s} {1:s}={2:s}'.format(
          path_string, hash_name, hash_value)
    return path_string

  def CompileReport(self, analysis_mediator):
    """Compiles an analysis report.

    Args:
      analysis_mediator: the analysis mediator object (instance of
                         AnalysisMediator).

    Returns:
      The analysis report (instance of AnalysisReport).
    """
    lines_of_text = [u'Listing file paths and hashes']
    for pathspec, hashes in sorted(
        self._paths_with_hashes.items(),
        key=lambda tuple: tuple[0].comparable):

      path_string = self._GeneratePathString(
          analysis_mediator, pathspec, hashes)
      lines_of_text.append(path_string)

    lines_of_text.append(u'')
    report_text = u'\n'.join(lines_of_text)
    return reports.AnalysisReport(self.NAME, text=report_text)


manager.AnalysisPluginManager.RegisterPlugin(FileHashesPlugin)
