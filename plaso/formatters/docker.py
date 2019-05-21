# -*- coding: utf-8 -*-
"""The Docker event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager


class DockerBaseEventFormatter(interface.ConditionalEventFormatter):
  """Class that contains common Docker event formatter functionality."""

  DATA_TYPE = 'docker:json'

  FORMAT_STRING_SHORT_PIECES = [
      '{id}']

  SOURCE_SHORT = 'DOCKER'


class DockerContainerLogEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Docker container log event"""

  DATA_TYPE = 'docker:json:container:log'

  FORMAT_STRING_SEPARATOR = ', '

  FORMAT_STRING_PIECES = (
      'Text: {log_line}',
      'Container ID: {container_id}',
      'Source: {log_source}',
  )

  SOURCE_LONG = 'Docker Container Logs'
  SOURCE_SHORT = 'DOCKER'


class DockerLayerEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Docker layer event."""

  DATA_TYPE = 'docker:json:layer'

  FORMAT_STRING_SEPARATOR = ', '

  FORMAT_STRING_PIECES = (
      'Command: {command}',
      'Layer ID: {layer_id}',
  )

  SOURCE_LONG = 'Docker Layer'
  SOURCE_SHORT = 'DOCKER'


class DockerContainerEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Docker event."""

  DATA_TYPE = 'docker:json:container'

  FORMAT_STRING_SEPARATOR = ', '

  FORMAT_STRING_PIECES = [
      'Action: {action}',
      'Container Name: {container_name}',
      'Container ID: {container_id}',
  ]

  SOURCE_LONG = 'Docker Container'
  SOURCE_SHORT = 'DOCKER'


manager.FormattersManager.RegisterFormatters([
    DockerContainerEventFormatter,
    DockerContainerLogEventFormatter,
    DockerLayerEventFormatter])
