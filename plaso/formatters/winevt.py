# -*- coding: utf-8 -*-
"""Windows EventLog custom event formatter helpers."""

import re

from plaso.formatters import interface
from plaso.formatters import logger
from plaso.formatters import manager


class WindowsEventLogMessageFormatterHelper(
    interface.CustomEventFormatterHelper):
  """Windows EventLog message formatter helper."""

  IDENTIFIER = 'windows_eventlog_message'

  _PARAMETER_REGEX = re.compile(r'^%%[1-9][0-9]*$')

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
        string_values = []
        for string_value in event_values.get('strings', []):
          if string_value is None:
            string_value = ''

          elif self._PARAMETER_REGEX.match(string_value):
            try:
              parameter_identifier = int(string_value[2:], 10)
              parameter_string = (
                  self._winevt_resources_helper.GetParameterString(
                      provider_identifier, source_name, parameter_identifier))
              if parameter_string:
                string_value = parameter_string

            except ValueError:
              pass

          string_values.append(string_value)

        try:
          message_string = message_string_template.format(*string_values)
        except (IndexError, TypeError) as exception:
          provider_identifier = provider_identifier or ''
          strings = ', '.join(string_values)
          logger.error((
              f'Unable to format message: 0x{message_identifier:08x} of '
              f'provider: {provider_identifier:s} template: '
              f'"{message_string_template:s}" and strings: "{strings:s}" '
              f'with error: {exception!s}'))
          # Unable to create the message string.
          # TODO: consider returning the unformatted message string.

    event_values['message_string'] = message_string


manager.FormattersManager.RegisterEventFormatterHelper(
    WindowsEventLogMessageFormatterHelper)
