# -*- coding: utf-8 -*-
"""Apple biome file parser plugin for App Launch."""
import blackboxprotobuf
from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers.biome_plugins import interface
from plaso.parsers import apple_biome


class ApplicationLaunchAppleBiomeEvent(events.EventData):
  """Application launch entry in Apple biome file.

  Attributes:
    event_time (dfdatetime.DateTimeValues): date and time when the application
        was launched.
    launcher (str): which process launched the application.
    launched_application (str): name of the launched application.
  """

  DATA_TYPE = 'apple:biome:app_launch'

  def __init__(self):
    """Initializes the event data."""
    super(
        ApplicationLaunchAppleBiomeEvent,
        self).__init__(data_type=self.DATA_TYPE)
    self.event_time = None
    self.launcher = None
    self.launched_application = None


class ApplicationLaunchBiomePlugin(interface.AppleBiomePlugin):
  """Parses an Application launch Apple biome file."""

  NAME = 'application_launch_biome'
  DATA_FORMAT = 'Biome application launch'

  REQUIRED_SCHEMA = {
      '1': {'type': 'string'},
      '2': {'type': 'int'},
      '3': {'type': 'int'},
      '4': {'type': 'fixed64'},
      '5': {'type': 'fixed64'},
      '6': {'type': 'string'},
      '9': {'type': 'string'},
      '10': {'type': 'string'}}

  # pylint: disable=unused-argument
  def Process(self, parser_mediator, biome_file=None, **unused_kwargs):
    """Extracts information from an Apple biome file. This is the main method
    that an Apple biome file plugin needs to implement.

    Args:
      parser_mediator (ParserMediator): parser mediator.
      biome_file (Optional[AppleBiomeFile]): Biome file.

    Raises:
      ValueError: If the file value is missing.
    """
    if biome_file is None:
      raise ValueError('Missing biome file.')

    for record in biome_file.records:
      content, _ = blackboxprotobuf.decode_message(record.protobuf)

      event_data = ApplicationLaunchAppleBiomeEvent()
      event_data.launcher = content.get('1')
      event_data.launched_application = content.get('6')
      event_data.event_time = dfdatetime_cocoa_time.CocoaTime(
          timestamp=record.timestamp1)

      parser_mediator.ProduceEventData(event_data)


apple_biome.AppleBiomeParser.RegisterPlugin(ApplicationLaunchBiomePlugin)
