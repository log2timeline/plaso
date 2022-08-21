# -*- coding: utf-8 -*-
"""Windows EventLog custom event formatter helpers."""

from plaso.formatters import interface
from plaso.formatters import logger
from plaso.formatters import manager


class WindowsEventLogMessageFormatterHelper(
    interface.CustomEventFormatterHelper):
  """Windows EventLog message formatter helper."""

  IDENTIFIER = 'windows_eventlog_message'

  def __init__(self):
    """Initialized a indows EventLog message formatter helper."""
    super(WindowsEventLogMessageFormatterHelper, self).__init__()
    self._winevt_resources_helper = None

  def FormatEventValues(self, output_mediator, event_values):
    """Formats event values using the helper.

    Args:
      output_mediator (OutputMediator): output mediator.
      event_values (dict[str, object]): event values.
    """
    if not self._winevt_resources_helper:
      self._winevt_resources_helper = output_mediator.GetWinevtResourcesHelper()

    message_string = None
    provider_identifier = event_values.get('provider_identifier', None)
    source_name = event_values.get('source_name', None)
    message_identifier = event_values.get('message_identifier', None)
    event_version = event_values.get('event_version', None)
    if (provider_identifier or source_name) and message_identifier:
      message_string_template = self._winevt_resources_helper.GetMessageString(
          provider_identifier, source_name, message_identifier, event_version)
      if message_string_template:
        string_values = [
            string or '' for string in event_values.get('strings', [])]

        try:
          message_string = message_string_template.format(*string_values)
        except (IndexError, TypeError) as exception:
          logger.error((
              'Unable to format message: 0x{0:08x} of provider: {1:s} '
              'template: "{2:s}" and strings: "{3:s}" with error: '
              '{4!s}').format(
                  message_identifier, provider_identifier or '',
                  message_string_template, ', '.join(string_values), exception))
          # Unable to create the message string.
          # TODO: consider returning the unformatted message string.

    event_values['message_string'] = message_string


manager.FormattersManager.RegisterEventFormatterHelper(
    WindowsEventLogMessageFormatterHelper)
