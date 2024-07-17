# -*- coding: utf-8 -*-
"""Windows EventLog providers helper."""


class WindowsEventLogProvidersHelper(object):
  """Windows EventLog providers helper."""

  def _GetNormalizedPath(self, path):
    """Retrieves a normalized variant of a path.

    Args:
      path (str): path of a message file.

    Returns:
      str: normalized path of a message file.
    """
    path_segments = path.split('\\')
    filename = path_segments.pop()

    if path_segments:
      # Check if the first path segment is a drive letter or "%SystemDrive%".
      first_path_segment = path_segments[0].lower()
      if ((len(first_path_segment) == 2 and first_path_segment[1:] == ':') or
          first_path_segment == '%systemdrive%'):
        path_segments[0] = ''

    path_segments_lower = [
        path_segment.lower() for path_segment in path_segments]

    if not path_segments_lower:
      # If the path is a filename assume the file is stored in:
      # "%SystemRoot%\System32".
      path_segments = ['%SystemRoot%', 'System32']

    elif path_segments_lower[0] in ('system32', '$(runtime.system32)'):
      # Note that the path can be relative so if it starts with "System32"
      # asume this represents "%SystemRoot%\System32".
      path_segments = ['%SystemRoot%', 'System32'] + path_segments[1:]

    elif path_segments_lower[0] in (
        '%systemroot%', '%windir%', '$(runtime.windows)'):
      path_segments = ['%SystemRoot%'] + path_segments[1:]

    # Check if path starts with "\SystemRoot\", "\Windows\" or "\WinNT\" for
    # example: "\SystemRoot\system32\drivers\SerCx.sys"
    elif (len(path_segments_lower) > 1 and not path_segments_lower[0] and
          path_segments_lower[1] in ('systemroot', 'windows', 'winnt')):
      path_segments = ['%SystemRoot%'] + path_segments[2:]

    path_segments.append(filename)
    return '\\'.join(path_segments) or '\\'

  def Merge(self, first_event_log_provider, second_event_log_provider):
    """Merges the information of the second Event Log provider into the first.

    Args:
      first_event_log_provider (EventLogProvider): first Event Log provider.
      second_event_log_provider (EventLogProvider): second Event Log provider.
    """
    if not first_event_log_provider.identifier:
      first_event_log_provider.identifier = second_event_log_provider.identifier
    elif (first_event_log_provider.identifier !=
          second_event_log_provider.identifier):
      first_event_log_provider.additional_identifier = (
          second_event_log_provider.identifier)

    for log_source in second_event_log_provider.log_sources:
      log_source = log_source.lower()
      if log_source not in first_event_log_provider.log_sources:
        first_event_log_provider.log_sources.append(log_source)

    for log_type in second_event_log_provider.log_types:
      log_type = log_type.lower()
      if log_type not in first_event_log_provider.log_types:
        first_event_log_provider.log_types.append(log_type)

    for path in second_event_log_provider.category_message_files:
      path = self._GetNormalizedPath(path)
      if path not in first_event_log_provider.category_message_files:
        first_event_log_provider.category_message_files.append(path)

    for path in second_event_log_provider.event_message_files:
      path = self._GetNormalizedPath(path)
      if path not in first_event_log_provider.event_message_files:
        first_event_log_provider.event_message_files.append(path)

    for path in second_event_log_provider.parameter_message_files:
      path = self._GetNormalizedPath(path)
      if path not in first_event_log_provider.parameter_message_files:
        first_event_log_provider.parameter_message_files.append(path)

  def NormalizeMessageFiles(self, event_log_provider):
    """Normalizes the message files.

    Args:
      event_log_provider (EventLogProvider): Event Log provider.
    """
    event_log_provider.category_message_files = [
        self._GetNormalizedPath(path)
        for path in event_log_provider.category_message_files]

    event_log_provider.event_message_files = [
        self._GetNormalizedPath(path)
        for path in event_log_provider.event_message_files]

    event_log_provider.parameter_message_files = [
        self._GetNormalizedPath(path)
        for path in event_log_provider.parameter_message_files]
