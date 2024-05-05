# -*- coding: utf-8 -*-
"""Apple biome file parser plugin for App Install."""
import blackboxprotobuf
from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers.biome_plugins import interface
from plaso.parsers import apple_biome


class ApplicationInstallAppleBiomeEvent(events.EventData):
  """Application install entry in Apple biome file.

  Attributes:
    event_time (dfdatetime.DateTimeValues): date and time when the application
        was launched.
    action_guid (str): GUID for the action of installing the application.
    action_name (str): name of the action.
    application_name (str): name of the application.
    bundle_identifier (str): bundle identifier of the application.
    event_time (dfdatetime.DateTimeValues): date and time when the application
        was installed.
  """

  DATA_TYPE = 'apple:biome:app_install'

  def __init__(self):
    """Initializes the event data."""
    super(
        ApplicationInstallAppleBiomeEvent,
        self).__init__(data_type=self.DATA_TYPE)
    self.action_guid = None
    self.action_name = None
    self.application_name = None
    self.bundle_identifier = None
    self.event_time = None


class ApplicationInstallBiomePlugin(interface.AppleBiomePlugin):
  """Parses an Application Install Apple biome file."""

  NAME = 'application_install_biome'
  DATA_FORMAT = 'Biome application install'

  REQUIRED_SCHEMA = {
      '1': {
          'type': 'message', 'message_typedef': {
              '1': {'type': 'string'},
              '2': {
                  'type': 'message', 'message_typedef': {
                      '1': {'type': 'int'},
                      '2': {'type': 'int'}},
                  'field_order': ['1', '2']}},
          'field_order': ['1', '2']},
      '2': {'type': 'fixed64'},
      '3': {'type': 'fixed64'},
      '4': {
          'type': 'message', 'message_typedef': {
              '1': {
                  'type': 'message', 'message_typedef': {
                      '1': {'type': 'int'},
                      '2': {'type': 'int'}},
                  'field_order': ['1', '2']},
              '3': {'type': 'string'}}, 'field_order': ['1', '3']},
      '5': {'type': 'string'},
      '7': {
          'type': 'message', 'message_typedef': {
              '1': {
                'type': 'message', 'message_typedef': {}, 'field_order': []},
              '2': {
                  'type': 'message', 'message_typedef': {
                      '1': {
                          'type': 'message', 'message_typedef': {
                              '1': {'type': 'int'},
                              '2': {'type': 'int'}},
                          'field_order': ['1', '2']},
                      '3': {'type': 'string'},
                      '4': {'type': 'int'}},
                  'field_order': ['1', '4']},
              '3': {'type': 'int'}},
          'field_order': ['1', '2', '3']},
      '8': {'type': 'fixed64'},
      '10': {'type': 'int'}}

  # pylint: disable=unused-argument
  def Process(self, parser_mediator, biome_file=None, **unused_kwargs):
    """Extracts information from an Apple biome file. This is the main method
    that an Apple biome file plugin needs to implement.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      biome_file (Optional[AppleBiomeFile]): Biome file.
    """
    if biome_file is None:
      raise ValueError('Missing biome file.')

    for record in biome_file.records:
      content, _ = blackboxprotobuf.decode_message(record.protobuf)

      event_data = ApplicationInstallAppleBiomeEvent()
      event_data.action_guid = content.get('5')
      event_data.action_name = content.get('1', {}).get('1')

      application_information = content.get('7', [])
      if application_information and isinstance(application_information, list):
        event_data.application_name = application_information[0].get(
            '2', {}).get('3')
        if not isinstance(event_data.application_name, str):
          event_data.application_name = None

      event_data.bundle_identifier = content.get('4', {}).get('3')
      event_data.event_time = dfdatetime_cocoa_time.CocoaTime(
          timestamp=record.timestamp1)

      parser_mediator.ProduceEventData(event_data)


apple_biome.AppleBiomeParser.RegisterPlugin(ApplicationInstallBiomePlugin)
