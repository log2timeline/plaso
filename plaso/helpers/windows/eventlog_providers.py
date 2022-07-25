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

    if path_segments:
      # Check if the first path segment is a drive letter or "%SystemDrive%".
      first_path_segment = path_segments[0].lower()
      if ((len(first_path_segment) == 2 and first_path_segment[1:] == ':') or
          first_path_segment == '%systemdrive%'):
        path_segments[0] = ''

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
      path = self._GetNormalizedPath(path.lower())
      if path not in first_event_log_provider.category_message_files:
        first_event_log_provider.category_message_files.append(path)

    for path in second_event_log_provider.event_message_files:
      path = self._GetNormalizedPath(path.lower())
      if path not in first_event_log_provider.event_message_files:
        first_event_log_provider.event_message_files.append(path)

    for path in second_event_log_provider.parameter_message_files:
      path = self._GetNormalizedPath(path.lower())
      if path not in first_event_log_provider.parameter_message_files:
        first_event_log_provider.parameter_message_files.append(path)

  def NormalizeMessageFiles(self, event_log_provider):
    """Normalizes the message files.

    Args:
      event_log_provider (EventLogProvider): Event Log provider.
    """
    event_log_provider.category_message_files = [
        self._GetNormalizedPath(path.lower())
        for path in event_log_provider.category_message_files]

    event_log_provider.event_message_files = [
        self._GetNormalizedPath(path.lower())
        for path in event_log_provider.event_message_files]

    event_log_provider.parameter_message_files = [
        self._GetNormalizedPath(path.lower())
        for path in event_log_provider.parameter_message_files]
