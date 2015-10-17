# -*- coding: utf-8 -*-
"""Parser for the Android usage-history.xml files."""

import os

from xml.etree import ElementTree

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.parsers import interface
from plaso.parsers import manager


class AndroidAppUsageEvent(time_events.JavaTimeEvent):
  """Convenience class for an Android Application Last Resumed event."""

  DATA_TYPE = u'android:event:last_resume_time'

  def __init__(self, java_time, package_name, component_name):
    """Initializes the event object.

    Args:
      java_time: the Java timestamp which is an integer containing the number
                 of milli seconds since January 1, 1970, 00:00:00 UTC.
      package_name: string containing the name of the Android application.
      component_name: string containing the name of the individual component
                      of the application.
    """
    super(AndroidAppUsageEvent, self).__init__(
        java_time, eventdata.EventTimestamp.LAST_RESUME_TIME)
    self.component = component_name
    self.package = package_name


class AndroidAppUsageParser(interface.SingleFileBaseParser):
  """Parses the Android usage-history.xml file."""

  NAME = u'android_app_usage'
  DESCRIPTION = u'Parser for Android usage-history.xml files.'

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses an Android usage-history file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    data = file_object.read(128)
    if not data.startswith(b'<?xml'):
      raise errors.UnableToParseFile(
          u'Not an Android usage history file [not XML]')

    _, _, data = data.partition(b'\n')
    if not data.startswith(b'<usage-history'):
      raise errors.UnableToParseFile(
          u'Not an Android usage history file [wrong XML root key]')

    # The current offset of the file-like object needs to point at
    # the start of the file for ElementTree to parse the XML data correctly.
    file_object.seek(0, os.SEEK_SET)

    xml = ElementTree.parse(file_object)
    root_node = xml.getroot()

    for application_node in root_node:
      package_name = application_node.get(u'name', u'')

      for part_node in application_node.iter():
        if part_node.tag != u'comp':
          continue

        component_name = part_node.get(u'name', u'')
        last_resume_time = part_node.get(u'lrt', None)

        if last_resume_time is None:
          parser_mediator.ProduceParseError(u'missing last resume time.')
          continue

        try:
          last_resume_time = int(last_resume_time, 10)
        except ValueError:
          parser_mediator.ProduceParseError(
              u'unsupported last resume time: {0:s}.'.format(last_resume_time))
          continue

        event_object = AndroidAppUsageEvent(
            last_resume_time, package_name, component_name)
        parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParser(AndroidAppUsageParser)
