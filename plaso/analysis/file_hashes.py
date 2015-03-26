# -*- coding: utf-8 -*-
"""A plugin to generate a list of unique hashes and paths."""

from plaso.analysis import interface
from plaso.lib import event


class FileHashesPlugin(interface.AnalysisPlugin):
  """A plugin for generate a list of file paths and corresponding hashes."""

  NAME = 'file_hashes'

  # Indicate that we can run this plugin during regular extraction.
  ENABLE_IN_EXTRACTION = True

  # We need to implement the interface for analysis plugins, but we don't use
  # command line options here, so disable checking for unused args.
  # pylint: disable=unused-argument
  def __init__(self, incoming_queue, options=None):
    """Initializes the unique hashes plugin.

    Args:
      incoming_queue: A queue to read events from.
      options: Optional command line arguments (instance of
      argparse.Namespace). The default is None.
    """
    super(FileHashesPlugin, self).__init__(incoming_queue)
    self._paths_with_hashes = {}

  def ExamineEvent(self, analysis_context, event_object, **kwargs):
    """Analyzes an event_object and creates Windows Services as required.

    Args:
      analysis_context: The analysis context object. Instance of
                        AnalysisContext.
      event_object: The event object (instance of EventObject) to examine.
    """
    pathspec = getattr(event_object, 'pathspec', None)
    if pathspec is None:
      return
    if self._paths_with_hashes.get(pathspec, None):
      # We've already processed an event with this pathspec and extracted the
      # hashes from it.
      return
    hash_attributes = {}
    for attr_name in event_object.GetAttributes():
      if attr_name.endswith(u'_hash'):
        hash_attributes[attr_name] = getattr(event_object, attr_name)
    self._paths_with_hashes[pathspec] = hash_attributes

  def _GeneratePathString(self, analysis_context, pathspec, hashes):
    """Generates a string containing a pathspec and its hashes.

    Args:
      analysis_context: The analysis context object. Instance of
                        AnalysisContext.
      pathspec: The PathSpec (instance of dfVFS.PathSpec) to generate a
                string for.
      hashes: A dict mapping hash attribute names to the value of that hash for
              the pathspec being processed.

    Returns:
      A string of the form "OS:/path/spec: test_hash=4".
    """
    display_name = analysis_context.GetDisplayName(pathspec)
    path_string = u'{0:s}:'.format(display_name)
    for hash_name, hash_value in sorted(hashes.items()):
      path_string = u'{0:s} {1:s}={2:s}'.format(
          path_string, hash_name, hash_value)
    return path_string

  def CompileReport(self, analysis_context):
    """Compiles a report of the analysis.

    Args:
      analysis_context: The analysis context object. Instance of
                        AnalysisContext.
    Returns:
      The analysis report (instance of AnalysisReport).
    """
    report = event.AnalysisReport(self.NAME)
    lines_of_text = [u'Listing file paths and hashes']
    for pathspec, hashes in sorted(self._paths_with_hashes.items(), key=lambda
        tuple: tuple[0].comparable):
      path_string = self._GeneratePathString(analysis_context, pathspec, hashes)
      lines_of_text.append(path_string)
    report.SetText(lines_of_text)

    return report
