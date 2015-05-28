# -*- coding: utf-8 -*-
"""This file contains a parser for the Android usage-history.xml file."""

import os

from xml.etree import ElementTree
from dfvfs.helpers import text_file

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager


class AndroidAppUsageEvent(event.EventObject):
  """EventObject for an Android Application Last Resumed event."""

  DATA_TYPE = u'android:event:last_resume_time'

  def __init__(self, last_resume_time, package, component):
    """Initializes the event object.

    Args:
      last_resume_time: The Last Resume Time of an Android App with details of
           individual components. The timestamp contains the number of
           milliseconds since Jan 1, 1970 00:00:00 UTC.
      package: The name of the Android App.
      component: The individual component of the App.
    """
    super(AndroidAppUsageEvent, self).__init__()
    self.timestamp = timelib.Timestamp.FromJavaTime(last_resume_time)
    self.package = package
    self.component = component

    self.timestamp_desc = eventdata.EventTimestamp.LAST_RESUME_TIME


class AndroidAppUsageParser(interface.SingleFileBaseParser):
  """Parses the Android usage-history.xml file."""

  _INITIAL_FILE_OFFSET = None

  NAME = u'android_app_usage'
  DESCRIPTION = u'Parser for the Android usage-history.xml file.'

  def ParseFileObject(self, parser_mediator, file_object, **kwargs):
    """Parses an Android usage-history file-like object.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      file_object: A file-like object.

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """
    file_object.seek(0, os.SEEK_SET)
    text_file_object = text_file.TextFile(file_object)

    # Need to verify the first line to make sure this is a) XML and
    # b) the right XML.
    first_line = text_file_object.readline(90)

    # Note that we must check the data here as a string first, otherwise
    # forcing first_line to convert to Unicode can raise a UnicodeDecodeError.
    if not first_line.startswith(b'<?xml'):
      raise errors.UnableToParseFile(
          u'Not an Android usage history file [not XML]')

    # We read in the second line due to the fact that ElementTree
    # reads the entire file in memory to parse the XML string and
    # we only care about the XML file with the correct root key,
    # which denotes a typed_history.xml file.
    second_line = text_file_object.readline(50).strip()

    # Note that we must check the data here as a string first, otherwise
    # forcing second_line to convert to Unicode can raise a UnicodeDecodeError.
    if second_line != b'<usage-history>':
      raise errors.UnableToParseFile(
          u'Not an Android usage history file [wrong XML root key]')

    # The current offset of the file-like object needs to point at
    # the start of the file for ElementTree to parse the XML data correctly.
    file_object.seek(0, os.SEEK_SET)

    xml = ElementTree.parse(file_object)
    root = xml.getroot()

    for app in root:
      for part in app.iter():
        if part.tag == u'comp':
          package = app.get(u'name', u'')
          component = part.get(u'name', u'')

          try:
            last_resume_time = int(part.get(u'lrt', u''), 10)
          except ValueError:
            continue

          event_object = AndroidAppUsageEvent(
              last_resume_time, package, component)
          parser_mediator.ProduceEvent(event_object)


manager.ParsersManager.RegisterParser(AndroidAppUsageParser)
