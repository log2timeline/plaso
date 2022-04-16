# -*- coding: utf-8 -*-
"""Parser for Docker configuration and log files."""

import codecs
import json
import os

from dfdatetime import semantic_time as dfdatetime_semantic_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.parsers import manager
from plaso.parsers import interface


class DockerJSONLayerEventData(events.EventData):
  """Docker file system layer configuration event data.

  Attributes:
    command: the command used which made Docker create a new layer.
    layer_id: the identifier of the current Docker layer (SHA-1).
  """

  DATA_TYPE = 'docker:json:layer'

  def __init__(self):
    """Initializes event data."""
    super(DockerJSONLayerEventData, self).__init__(data_type=self.DATA_TYPE)
    self.command = None
    self.layer_id = None


class DockerJSONParser(interface.FileObjectParser):
  """Parser for Docker json configuration and log files.

  This handles :
  * Filesystem layer config files
    DOCKER_DIR/graph/<layer_id>/json
  """

  NAME = 'dockerjson'
  DATA_FORMAT = 'Docker configuration and log JSON file'

  _ENCODING = 'utf-8'

  def _GetIdentifierFromPath(self, parser_mediator):
    """Extracts a container or a graph ID from a JSON file's path.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.

    Returns:
      str: container or graph identifier.
    """
    file_entry = parser_mediator.GetFileEntry()
    path = file_entry.path_spec.location
    file_system = file_entry.GetFileSystem()
    path_segments = file_system.SplitPath(path)
    return path_segments[-2]

  def _ParseLayerConfigJSON(self, parser_mediator, file_object):
    """Extracts events from a Docker filesystem layer configuration file.

    The path of each filesystem layer config file is:
    DOCKER_DIR/graph/<layer_id>/json

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file is not a valid layer config file.
    """
    file_content = file_object.read()
    file_content = codecs.decode(file_content, self._ENCODING)

    json_dict = json.loads(file_content)

    if 'docker_version' not in json_dict:
      raise errors.WrongParser(
          'not a valid Docker layer configuration file, missing '
          '\'docker_version\' key.')

    time_string = json_dict.get('created', None)
    if time_string is not None:
      layer_creation_command_array = [
          x.strip() for x in json_dict['container_config']['Cmd']]
      layer_creation_command = ' '.join(layer_creation_command_array).replace(
          '\t', '')

      event_data = DockerJSONLayerEventData()
      event_data.command = layer_creation_command
      event_data.layer_id = self._GetIdentifierFromPath(parser_mediator)

      try:
        date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
        date_time.CopyFromStringISO8601(time_string)
      except ValueError as exception:
        parser_mediator.ProduceExtractionWarning((
            'Unable to parse created time string: {0:s} with error: '
            '{1!s}').format(time_string, exception))
        date_time = dfdatetime_semantic_time.InvalidTime()

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_ADDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses various Docker configuration and log files in JSON format.

    This method checks whether the file_object points to a docker JSON config
    or log file, and calls the corresponding _Parse* function to generate
    Events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): a file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
      ValueError: if the JSON file cannot be decoded.
    """
    # Trivial JSON format check: first character must be an open brace.
    if file_object.read(1) != b'{':
      raise errors.WrongParser(
          'is not a valid JSON file, missing opening brace.')

    file_object.seek(0, os.SEEK_SET)

    file_entry = parser_mediator.GetFileEntry()

    file_system = file_entry.GetFileSystem()

    json_file_path = parser_mediator.GetDisplayName()
    split_path = file_system.SplitPath(json_file_path)
    try:
      if 'containers' in split_path:
        pass

      elif 'graph' in split_path:
        if 'json' in split_path:
          self._ParseLayerConfigJSON(parser_mediator, file_object)

    except ValueError as exception:
      if exception == 'No JSON object could be decoded':
        raise errors.WrongParser(exception)
      raise


manager.ParsersManager.RegisterParser(DockerJSONParser)
