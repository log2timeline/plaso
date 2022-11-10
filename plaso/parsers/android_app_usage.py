# -*- coding: utf-8 -*-
"""Parser for the Android usage history (usage-history.xml) files."""

import os

from defusedxml import ElementTree

from dfdatetime import java_time as dfdatetime_java_time

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import interface
from plaso.parsers import manager


class AndroidAppUsageEventData(events.EventData):
  """Android application usage event data.

  Attributes:
    component (str): name of the individual component of the application.
    last_resume_time (dfdatetime.DateTimeValues): date and time the application
        was last resumed.
    package (str): name of the Android application.
  """

  DATA_TYPE = 'android:app_usage'

  def __init__(self):
    """Initializes event data."""
    super(AndroidAppUsageEventData, self).__init__(data_type=self.DATA_TYPE)
    self.component = None
    self.last_resume_time = None
    self.package = None


class AndroidAppUsageParser(interface.FileObjectParser):
  """Parses the Android usage history (usage-history.xml) file."""

  NAME = 'android_app_usage'
  DATA_FORMAT = 'Android usage history (usage-history.xml) file'

  _HEADER_READ_SIZE = 128

  def ParseFileObject(self, parser_mediator, file_object):
    """Parses an Android usage-history file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      file_object (dfvfs.FileIO): file-like object.

    Raises:
      WrongParser: when the file cannot be parsed.
    """
    data = file_object.read(self._HEADER_READ_SIZE)
    if not data.startswith(b'<?xml'):
      raise errors.WrongParser(
          'Not an Android usage history file [not XML]')

    _, _, data = data.partition(b'\n')
    if not data.startswith(b'<usage-history'):
      raise errors.WrongParser(
          'Not an Android usage history file [wrong XML root key]')

    # The current offset of the file-like object needs to point at
    # the start of the file for ElementTree to parse the XML data correctly.
    file_object.seek(0, os.SEEK_SET)

    xml = ElementTree.parse(file_object)
    root_node = xml.getroot()

    for application_node in root_node:
      package_name = application_node.get('name', None)

      for part_node in application_node.iter():
        if part_node.tag != 'comp':
          continue

        last_resume_time = part_node.get('lrt', None)
        if last_resume_time is None:
          parser_mediator.ProduceExtractionWarning('missing last resume time.')
          continue

        try:
          last_resume_time = int(last_resume_time, 10)
        except ValueError:
          parser_mediator.ProduceExtractionWarning(
              'unsupported last resume time: {0:s}.'.format(last_resume_time))
          continue

        event_data = AndroidAppUsageEventData()
        event_data.component = part_node.get('name', None)
        event_data.last_resume_time = dfdatetime_java_time.JavaTime(
            timestamp=last_resume_time)
        event_data.package = package_name

        parser_mediator.ProduceEventData(event_data)


manager.ParsersManager.RegisterParser(AndroidAppUsageParser)
