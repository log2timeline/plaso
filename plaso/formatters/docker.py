# -*- coding: utf-8 -*-
"""The Docker event formatter."""

from plaso.formatters import interface
from plaso.formatters import manager


class DockerBaseEventFormatter(interface.ConditionalEventFormatter):
  """Class that contains common Docker event formatter functionality."""

  DATA_TYPE = u'docker:json'

  FORMAT_STRING_SHORT_PIECES = [
      u'{id}']

  SOURCE_SHORT = u'DOCKER'


class DockerContainerLogEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Docker container log event"""

  DATA_TYPE = u'docker:json:container:log'

  FORMAT_STRING_SEPARATOR = u', '

  FORMAT_STRING_PIECES = (
      u'Text: {log_line}',
      u'Container ID: {container_id}',
      u'Source: {log_source}',
  )

  SOURCE_LONG = u'Docker Container Logs'
  SOURCE_SHORT = u'DOCKER'


class DockerLayerEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Docker layer event."""

  DATA_TYPE = u'docker:json:layer'

  FORMAT_STRING_SEPARATOR = u', '

  FORMAT_STRING_PIECES = (
      u'Command: {command}',
      u'Layer ID: {layer_id}',
  )

  SOURCE_LONG = u'Docker Layer'
  SOURCE_SHORT = u'DOCKER'


class DockerContainerEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Docker event."""

  DATA_TYPE = u'docker:json:container'

  FORMAT_STRING_SEPARATOR = u', '

  FORMAT_STRING_PIECES = [
      u'Action: {action}',
      u'Container Name: {container_name}',
      u'Container ID: {container_id}',
  ]

  SOURCE_LONG = u'Docker Container'
  SOURCE_SHORT = u'DOCKER'


manager.FormattersManager.RegisterFormatters([
    DockerContainerEventFormatter,
    DockerContainerLogEventFormatter,
    DockerLayerEventFormatter,
])
