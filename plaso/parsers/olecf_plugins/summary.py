# -*- coding: utf-8 -*-
"""Plugin to parse the OLECF summary/document summary information items."""

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.parsers import olecf
from plaso.parsers.olecf_plugins import interface


class OleCfSummaryInfoEvent(time_events.FiletimeEvent):
  """Convenience class for an OLECF Summary info event."""

  DATA_TYPE = u'olecf:summary_info'

  def __init__(self, timestamp, usage, attributes):
    """Initializes the event.

    Args:
      timestamp: The FILETIME timestamp value.
      usage: The usage string, describing the timestamp value.
      attributes: A dict object containing all extracted attributes.
    """
    super(OleCfSummaryInfoEvent, self).__init__(
        timestamp, usage)

    self.name = u'Summary Information'

    for attribute_name, attribute_value in attributes.iteritems():
      setattr(self, attribute_name, attribute_value)


# TODO: Move this class to a higher level (to the interface)
# so the these functions can be shared by other plugins.
class OleCfSummaryInfo(object):
  """An OLECF Summary Info object."""

  _CLASS_IDENTIFIER = u'f29f85e0-4ff9-1068-ab91-08002b27b3d9'

  _PROPERTY_NAMES_INT32 = {
      0x000e: u'number_of_pages',  # PIDSI_PAGECOUNT
      0x000f: u'number_of_words',  # PIDSI_WORDCOUNT
      0x0010: u'number_of_characters',  # PIDSI_CHARCOUNT
      0x0013: u'security',  # PIDSI_SECURITY
  }

  _PROPERTY_NAMES_STRING = {
      0x0002: u'title',  # PIDSI_TITLE
      0x0003: u'subject',  # PIDSI_SUBJECT
      0x0004: u'author',  # PIDSI_AUTHOR
      0x0005: u'keywords',  # PIDSI_KEYWORDS
      0x0006: u'comments',  # PIDSI_COMMENTS
      0x0007: u'template',  # PIDSI_TEMPLATE
      0x0008: u'last_saved_by',  # PIDSI_LASTAUTHOR
      0x0009: u'revision_number',  # PIDSI_REVNUMBER
      0x0012: u'application',  # PIDSI_APPNAME
  }

  PIDSI_CODEPAGE = 0x0001
  PIDSI_EDITTIME = 0x000a
  PIDSI_LASTPRINTED = 0x000b
  PIDSI_CREATE_DTM = 0x000c
  PIDSI_LASTSAVE_DTM = 0x000d
  PIDSI_THUMBNAIL = 0x0011

  def __init__(self, olecf_item):
    """Initialize the OLECF summary object.

    Args:
      olecf_item: The OLECF item (instance of pyolecf.property_set_stream).
    """
    super(OleCfSummaryInfo, self).__init__()
    self.attributes = {}
    self.events = []

    self._InitFromPropertySet(olecf_item.set)

  def _InitFromPropertySet(self, property_set):
    """Initializes the object from a property set.

    Args:
      property_set: The OLECF property set (pyolecf.property_set).
    """
    # Combine the values of multiple property sections
    # but do not override properties that are already set.
    for property_section in property_set.sections:
      if property_section.class_identifier != self._CLASS_IDENTIFIER:
        continue
      for property_value in property_section.properties:
        self._InitFromPropertyValue(property_value)

  def _InitFromPropertyValue(self, property_value):
    """Initializes the object from a property value.

    Args:
      property_value: The OLECF property value (pyolecf.property_value).
    """
    if property_value.type == interface.OleDefinitions.VT_I2:
      self._InitFromPropertyValueTypeInt16(property_value)

    elif property_value.type == interface.OleDefinitions.VT_I4:
      self._InitFromPropertyValueTypeInt32(property_value)

    elif (property_value.type == interface.OleDefinitions.VT_LPSTR or
          property_value.type == interface.OleDefinitions.VT_LPWSTR):
      self._InitFromPropertyValueTypeString(property_value)

    elif property_value.type == interface.OleDefinitions.VT_FILETIME:
      self._InitFromPropertyValueTypeFiletime(property_value)

  def _InitFromPropertyValueTypeInt16(self, property_value):
    """Initializes the object from a 16-bit int type property value.

    Args:
      property_value: The OLECF property value (pyolecf.property_value
                      of type VT_I2).
    """
    if property_value.identifier == self.PIDSI_CODEPAGE:
      # TODO: can the codepage vary per property section?
      # And is it needed to interpret the ASCII strings?
      # codepage = property_value.data_as_integer
      pass

  def _InitFromPropertyValueTypeInt32(self, property_value):
    """Initializes the object from a 32-bit int type property value.

    Args:
      property_value: The OLECF property value (pyolecf.property_value
                      of type VT_I4).
    """
    property_name = self._PROPERTY_NAMES_INT32.get(
        property_value.identifier, None)

    if property_name and not property_name in self.attributes:
      self.attributes[property_name] = property_value.data_as_integer

  def _InitFromPropertyValueTypeString(self, property_value):
    """Initializes the object from a string type property value.

    Args:
      property_value: The OLECF property value (pyolecf.property_value
                      of type VT_LPSTR or VT_LPWSTR).
    """
    property_name = self._PROPERTY_NAMES_STRING.get(
        property_value.identifier, None)

    if property_name and not property_name in self.attributes:
      self.attributes[property_name] = property_value.data_as_string

  def _InitFromPropertyValueTypeFiletime(self, property_value):
    """Initializes the object from a filetime type property value.

    Args:
      property_value: The OLECF property value (pyolecf.property_value
                      of type VT_FILETIME).
    """
    if property_value.identifier == self.PIDSI_LASTPRINTED:
      self.events.append(
          (property_value.data_as_integer, u'Document Last Printed Time'))

    elif property_value.identifier == self.PIDSI_CREATE_DTM:
      self.events.append(
          (property_value.data_as_integer, u'Document Creation Time'))

    elif property_value.identifier == self.PIDSI_LASTSAVE_DTM:
      self.events.append(
          (property_value.data_as_integer, u'Document Last Save Time'))

    elif property_value.identifier == self.PIDSI_EDITTIME:
      # property_name = u'total_edit_time'
      # TODO: handle duration.
      pass


class OleCfDocumentSummaryInfoEvent(time_events.FiletimeEvent):
  """Convenience class for an OLECF Document Summary info event."""

  DATA_TYPE = u'olecf:document_summary_info'

  _CLASS_IDENTIFIER = u'd5cdd502-2e9c-101b-9397-08002b2cf9ae'

  _PROPERTY_NAMES_BOOL = {
      0x0013: u'shared_document',  # PIDDSI_SHAREDDOC
  }

  _PROPERTY_NAMES_INT32 = {
      0x0004: u'number_of_bytes',  # PIDDSI_BYTECOUNT
      0x0005: u'number_of_lines',  # PIDDSI_LINECOUNT
      0x0006: u'number_of_paragraphs',  # PIDDSI_PARCOUNT
      0x0007: u'number_of_slides',  # PIDDSI_SLIDECOUNT
      0x0008: u'number_of_notes',  # PIDDSI_NOTECOUNT
      0x0009: u'number_of_hidden_slides',  # PIDDSI_HIDDENCOUNT
      0x000a: u'number_of_clips',  # PIDDSI_MMCLIPCOUNT
      0x0011: u'number_of_characters_with_white_space',  # PIDDSI_CCHWITHSPACES
      0x0017: u'application_version',  # PIDDSI_VERSION
  }

  _PROPERTY_NAMES_STRING = {
      0x000e: u'manager',  # PIDDSI_MANAGER
      0x000f: u'company',  # PIDDSI_COMPANY
      0x001a: u'content_type',  # PIDDSI_CONTENTTYPE
      0x001b: u'content_status',  # PIDDSI_CONTENTSTATUS
      0x001c: u'language',  # PIDDSI_LANGUAGE
      0x001d: u'document_version',  # PIDDSI_DOCVERSION
  }

  PIDDSI_CODEPAGE = 0x0001
  PIDDSI_CATEGORY = 0x0002
  PIDDSI_PRESFORMAT = 0x0003
  PIDDSI_SCALE = 0x000b
  PIDDSI_HEADINGPAIR = 0x000c
  PIDDSI_DOCPARTS = 0x000d
  PIDDSI_LINKSDIRTY = 0x0010
  PIDDSI_VERSION = 0x0017

  def __init__(self, timestamp, usage, olecf_item):
    """Initializes the event.

    Args:
      timestamp: The FILETIME timestamp value.
      usage: The usage string, describing the timestamp value.
      olecf_item: The OLECF item (pyolecf.property_set_stream).
    """
    super(OleCfDocumentSummaryInfoEvent, self).__init__(
        timestamp, usage)

    self.name = u'Document Summary Information'

    self._InitFromPropertySet(olecf_item.set)

  def _InitFromPropertySet(self, property_set):
    """Initializes the event from a property set.

    Args:
      property_set: The OLECF property set (pyolecf.property_set).
    """
    # Combine the values of multiple property sections
    # but do not override properties that are already set.
    for property_section in property_set.sections:
      if property_section.class_identifier != self._CLASS_IDENTIFIER:
        continue
      for property_value in property_section.properties:
        self._InitFromPropertyValue(property_value)

  def _InitFromPropertyValue(self, property_value):
    """Initializes the event from a property value.

    Args:
      property_value: The OLECF property value (pyolecf.property_value).
    """
    if property_value.type == interface.OleDefinitions.VT_I2:
      self._InitFromPropertyValueTypeInt16(property_value)

    elif property_value.type == interface.OleDefinitions.VT_I4:
      self._InitFromPropertyValueTypeInt32(property_value)

    elif property_value.type == interface.OleDefinitions.VT_BOOL:
      self._InitFromPropertyValueTypeBool(property_value)

    elif (property_value.type == interface.OleDefinitions.VT_LPSTR or
          property_value.type == interface.OleDefinitions.VT_LPWSTR):
      self._InitFromPropertyValueTypeString(property_value)

  def _InitFromPropertyValueTypeInt16(self, property_value):
    """Initializes the event from a 16-bit int type property value.

    Args:
      property_value: The OLECF property value (pyolecf.property_value
                      of type VT_I2).
    """
    if property_value.identifier == self.PIDDSI_CODEPAGE:
      # TODO: can the codepage vary per property section?
      # And is it needed to interpret the ASCII strings?
      # codepage = property_value.data_as_integer
      pass

  def _InitFromPropertyValueTypeInt32(self, property_value):
    """Initializes the event from a 32-bit int type property value.

    Args:
      property_value: The OLECF property value (pyolecf.property_value
                      of type VT_I4).
    """
    property_name = self._PROPERTY_NAMES_INT32.get(
        property_value.identifier, None)

    # The application version consists of 2 16-bit values that make up
    # the version number. Where the upper 16-bit is the major number
    # and the lower 16-bit the minor number.
    if property_value.identifier == self.PIDDSI_VERSION:
      application_version = property_value.data_as_integer
      setattr(self, property_name, u'{0:d}.{1:d}'.format(
          application_version >> 16, application_version & 0xffff))

    elif property_name and not hasattr(self, property_name):
      setattr(self, property_name, property_value.data_as_integer)

  def _InitFromPropertyValueTypeBool(self, property_value):
    """Initializes the event from a boolean type property value.

    Args:
      property_value: The OLECF property value (pyolecf.property_value
                      of type VT_BOOL).
    """
    property_name = self._PROPERTY_NAMES_BOOL.get(
        property_value.identifier, None)

    if property_name and not hasattr(self, property_name):
      setattr(self, property_name, property_value.data_as_boolean)

  def _InitFromPropertyValueTypeString(self, property_value):
    """Initializes the event from a string type property value.

    Args:
      property_value: The OLECF property value (pyolecf.property_value
                      of type VT_LPSTR or VT_LPWSTR).
    """
    property_name = self._PROPERTY_NAMES_STRING.get(
        property_value.identifier, None)

    if property_name and not hasattr(self, property_name):
      setattr(self, property_name, property_value.data_as_string)


class DocumentSummaryOlecfPlugin(interface.OlecfPlugin):
  """Plugin that parses DocumentSummaryInformation item from an OLECF file."""

  NAME = u'olecf_document_summary'
  DESCRIPTION = u'Parser for a DocumentSummaryInformation OLECF stream.'

  # pylint: disable=anomalous-backslash-in-string
  REQUIRED_ITEMS = frozenset([u'\005DocumentSummaryInformation'])

  def ParseItems(
      self, parser_mediator, root_item=None, items=None, **unused_kwargs):
    """Parses a document summary information OLECF item.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      root_item: Optional root item of the OLECF file. The default is None.
      item_names: Optional list of all items discovered in the root.
                  The default is None.
    """
    root_creation_time, root_modification_time = self.GetTimestamps(root_item)

    for item in items:
      if root_creation_time:
        event_object = OleCfDocumentSummaryInfoEvent(
            root_creation_time, eventdata.EventTimestamp.CREATION_TIME, item)
        parser_mediator.ProduceEvent(event_object)

      if root_modification_time:
        event_object = OleCfDocumentSummaryInfoEvent(
            root_modification_time, eventdata.EventTimestamp.MODIFICATION_TIME,
            item)
        parser_mediator.ProduceEvent(event_object)


class SummaryInfoOlecfPlugin(interface.OlecfPlugin):
  """Plugin that parses the SummaryInformation item from an OLECF file."""

  NAME = u'olecf_summary'
  DESCRIPTION = u'Parser for a SummaryInformation OLECF stream.'

  # pylint: disable=anomalous-backslash-in-string
  REQUIRED_ITEMS = frozenset([u'\005SummaryInformation'])

  def ParseItems(
      self, parser_mediator, root_item=None, items=None, **unused_kwargs):
    """Parses a summary information OLECF item.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      root_item: Optional root item of the OLECF file. The default is None.
      item_names: Optional list of all items discovered in the root.
                  The default is None.
    """
    root_creation_time, root_modification_time = self.GetTimestamps(root_item)

    for item in items:
      summary_information_object = OleCfSummaryInfo(item)

      for timestamp, timestamp_description in summary_information_object.events:
        event_object = OleCfSummaryInfoEvent(
            timestamp, timestamp_description,
            summary_information_object.attributes)
        parser_mediator.ProduceEvent(event_object)

      if root_creation_time:
        event_object = OleCfSummaryInfoEvent(
            root_creation_time, eventdata.EventTimestamp.CREATION_TIME,
            summary_information_object.attributes)
        parser_mediator.ProduceEvent(event_object)

      if root_modification_time:
        event_object = OleCfSummaryInfoEvent(
            root_modification_time, eventdata.EventTimestamp.MODIFICATION_TIME,
            summary_information_object.attributes)
        parser_mediator.ProduceEvent(event_object)


olecf.OleCfParser.RegisterPlugins([
    DocumentSummaryOlecfPlugin, SummaryInfoOlecfPlugin])
