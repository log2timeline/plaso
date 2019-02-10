# -*- coding: utf-8 -*-
"""Plugin to parse the OLECF summary/document summary information items."""

from __future__ import unicode_literals

from dfdatetime import filetime as dfdatetime_filetime

import pyolecf

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import py2to3
from plaso.parsers import olecf
from plaso.parsers.olecf_plugins import interface


class OLECFPropertySetStream(object):
  """OLECF property set stream.

  Attributes:
    date_time_properties (dict[str, dfdatetime.DateTimeValues]): date and time
        properties and values.
  """
  _CLASS_IDENTIFIER = None

  _INTEGER_TYPES = frozenset([
      pyolecf.value_types.INTEGER_16BIT_SIGNED,
      pyolecf.value_types.INTEGER_32BIT_SIGNED,
      pyolecf.value_types.FILETIME])

  _STRING_TYPES = frozenset([
      pyolecf.value_types.STRING_ASCII,
      pyolecf.value_types.STRING_UNICODE])

  _DATE_TIME_PROPERTIES = frozenset([])

  _PROPERTY_NAMES = None
  _PROPERTY_VALUE_MAPPINGS = None

  def __init__(self, olecf_item):
    """Initialize an OLECF property set stream.

    Args:
      olecf_item (pyolecf.property_set_stream): OLECF item.
    """
    super(OLECFPropertySetStream, self).__init__()
    self._properties = {}
    self.date_time_properties = {}

    self._ReadPropertySet(olecf_item.set)

  def _GetValueAsObject(self, property_value):
    """Retrieves the property value as a Python object.

    Args:
      property_value (pyolecf.property_value): OLECF property value.

    Returns:
      object: property value as a Python object.
    """
    if property_value.type == pyolecf.value_types.BOOLEAN:
      return property_value.data_as_boolean

    if property_value.type in self._INTEGER_TYPES:
      return property_value.data_as_integer

    if property_value.type in self._STRING_TYPES:
      return property_value.data_as_string

    try:
      data = property_value.data
    except IOError:
      data = None

    return data

  def _ReadPropertySet(self, property_set):
    """Reads properties from a property set.

    Args:
      property_set (pyolecf.property_set): OLECF property set.
    """
    # Combine the values of multiple property sections
    # but do not override properties that are already set.
    for property_section in property_set.sections:
      if property_section.class_identifier != self._CLASS_IDENTIFIER:
        continue

      for property_value in property_section.properties:
        property_name = self._PROPERTY_NAMES.get(
            property_value.identifier, None)
        if not property_name:
          property_name = '0x{0:04}'.format(property_value.identifier)

        value = self._GetValueAsObject(property_value)
        if self._PROPERTY_VALUE_MAPPINGS:
          value_callback_name = self._PROPERTY_VALUE_MAPPINGS.get(
              property_name, None)
          if value_callback_name:
            value_callback_method = getattr(self, value_callback_name, None)
            if value_callback_method:
              value = value_callback_method(value)

        if property_name in self._DATE_TIME_PROPERTIES:
          properties_dict = self.date_time_properties
          value = dfdatetime_filetime.Filetime(timestamp=value)
        else:
          properties_dict = self._properties

        if property_name not in properties_dict:
          properties_dict[property_name] = value

  def GetEventData(self, data_type):
    """Retrieves the properties as event data.

    Args:
      data_type (str): event data type.

    Returns:
      EventData: event data.
    """
    event_data = events.EventData(data_type=data_type)
    for property_name, property_value in iter(self._properties.items()):
      if isinstance(property_value, py2to3.BYTES_TYPE):
        property_value = repr(property_value)
      setattr(event_data, property_name, property_value)

    return event_data


class OLECFDocumentSummaryInformationEvent(time_events.DateTimeValuesEvent):
  """Convenience class for an OLECF Document summary information event.

  Attributes:
    name (str): name of the OLECF item.
  """

  DATA_TYPE = 'olecf:document_summary_info'

  def __init__(self, date_time, date_time_description):
    """Initializes an event.

    Args:
      date_time (dfdatetime.DateTimeValues): date and time values.
      date_time_description (str): description of the meaning of the date
          and time values.
    """
    super(OLECFDocumentSummaryInformationEvent, self).__init__(
        date_time, date_time_description)
    self.name = 'Document Summary Information'


class OLECFSummaryInformationEvent(time_events.DateTimeValuesEvent):
  """Convenience class for an OLECF Summary information event.

  Attributes:
    name (str): name of the OLECF item.
  """

  DATA_TYPE = 'olecf:summary_info'

  def __init__(self, date_time, date_time_description):
    """Initializes an event.

    Args:
      date_time (dfdatetime.DateTimeValues): date and time values.
      date_time_description (str): description of the meaning of the date
          and time values.
    """
    super(OLECFSummaryInformationEvent, self).__init__(
        date_time, date_time_description)
    self.name = 'Summary Information'


class OLECFDocumentSummaryInformation(OLECFPropertySetStream):
  """OLECF Document Summary information property set."""

  _CLASS_IDENTIFIER = 'd5cdd502-2e9c-101b-9397-08002b2cf9ae'

  _PROPERTY_NAMES = {
      0x0001: 'codepage',  # PIDDSI_CODEPAGE
      0x0002: 'category',  # PIDDSI_CATEGORY
      0x0003: 'presentation_format',  # PIDDSI_PRESFORMAT
      0x0004: 'number_of_bytes',  # PIDDSI_BYTECOUNT
      0x0005: 'number_of_lines',  # PIDDSI_LINECOUNT
      0x0006: 'number_of_paragraphs',  # PIDDSI_PARCOUNT
      0x0007: 'number_of_slides',  # PIDDSI_SLIDECOUNT
      0x0008: 'number_of_notes',  # PIDDSI_NOTECOUNT
      0x0009: 'number_of_hidden_slides',  # PIDDSI_HIDDENCOUNT
      0x000a: 'number_of_clips',  # PIDDSI_MMCLIPCOUNT
      0x000b: 'scale',  # PIDDSI_SCALE
      0x000c: 'heading_pair',  # PIDDSI_HEADINGPAIR
      0x000d: 'document_parts',  # PIDDSI_DOCPARTS
      0x000e: 'manager',  # PIDDSI_MANAGER
      0x000f: 'company',  # PIDDSI_COMPANY
      0x0010: 'links_dirty',  # PIDDSI_LINKSDIRTY
      0x0011: 'number_of_characters_with_white_space',  # PIDDSI_CCHWITHSPACES
      0x0013: 'shared_document',  # PIDDSI_SHAREDDOC
      0x0017: 'application_version',  # PIDDSI_VERSION
      0x001a: 'content_type',  # PIDDSI_CONTENTTYPE
      0x001b: 'content_status',  # PIDDSI_CONTENTSTATUS
      0x001c: 'language',  # PIDDSI_LANGUAGE
      0x001d: 'document_version',  # PIDDSI_DOCVERSION
  }

  _PROPERTY_VALUE_MAPPINGS = {
      'application_version': '_FormatApplicationVersion',
  }

  def _FormatApplicationVersion(self, application_version):
    """Formats the application version.

    Args:
      application_version (int): application version.

    Returns:
      str: formatted application version.
    """
    # The application version consists of 2 16-bit values that make up
    # the version number. Where the upper 16-bit is the major number
    # and the lower 16-bit the minor number.
    return '{0:d}.{1:d}'.format(
        application_version >> 16, application_version & 0xffff)


class OLECFSummaryInformation(OLECFPropertySetStream):
  """OLECF Summary information property set."""

  _CLASS_IDENTIFIER = 'f29f85e0-4ff9-1068-ab91-08002b27b3d9'

  _DATE_TIME_PROPERTIES = frozenset([
      'creation_time', 'last_printed_time', 'last_save_time'])

  _PROPERTY_NAMES = {
      0x0001: 'codepage',  # PIDSI_CODEPAGE
      0x0002: 'title',  # PIDSI_TITLE
      0x0003: 'subject',  # PIDSI_SUBJECT
      0x0004: 'author',  # PIDSI_AUTHOR
      0x0005: 'keywords',  # PIDSI_KEYWORDS
      0x0006: 'comments',  # PIDSI_COMMENTS
      0x0007: 'template',  # PIDSI_TEMPLATE
      0x0008: 'last_saved_by',  # PIDSI_LASTAUTHOR
      0x0009: 'revision_number',  # PIDSI_REVNUMBER
      0x000a: 'edit_time',  # PIDSI_EDITTIME
      0x000b: 'last_printed_time',  # PIDSI_LASTPRINTED
      0x000c: 'creation_time',  # PIDSI_CREATE_DTM
      0x000d: 'last_save_time',  # PIDSI_LASTSAVE_DTM
      0x000e: 'number_of_pages',  # PIDSI_PAGECOUNT
      0x000f: 'number_of_words',  # PIDSI_WORDCOUNT
      0x0010: 'number_of_characters',  # PIDSI_CHARCOUNT
      0x0011: 'thumbnail',  # PIDSI_THUMBNAIL
      0x0012: 'application',  # PIDSI_APPNAME
      0x0013: 'security',  # PIDSI_SECURITY
  }


class DocumentSummaryInformationOLECFPlugin(interface.OLECFPlugin):
  """Plugin that parses DocumentSummaryInformation item from an OLECF file."""

  NAME = 'olecf_document_summary'
  DESCRIPTION = 'Parser for a DocumentSummaryInformation OLECF stream.'

  # pylint: disable=anomalous-backslash-in-string
  REQUIRED_ITEMS = frozenset(['\005DocumentSummaryInformation'])

  def Process(self, parser_mediator, root_item=None, **kwargs):
    """Parses a document summary information OLECF item.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      root_item (Optional[pyolecf.item]): root item of the OLECF file.

    Raises:
      ValueError: If the root item is not set.
    """
    # This will raise if unhandled keyword arguments are passed.
    super(DocumentSummaryInformationOLECFPlugin, self).Process(
        parser_mediator, **kwargs)

    if not root_item:
      raise ValueError('Root item not set.')

    root_creation_time, root_modification_time = self._GetTimestamps(root_item)

    for item_name in self.REQUIRED_ITEMS:
      item = root_item.get_sub_item_by_name(item_name)
      if not item:
        continue

      summary_information = OLECFDocumentSummaryInformation(item)
      event_data = summary_information.GetEventData(
          data_type='olecf:document_summary_info')
      event_data.name = 'Document Summary Information'

      if root_creation_time:
        date_time = dfdatetime_filetime.Filetime(
            timestamp=root_creation_time)
        event = OLECFDocumentSummaryInformationEvent(
            date_time, definitions.TIME_DESCRIPTION_CREATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      if root_modification_time:
        date_time = dfdatetime_filetime.Filetime(
            timestamp=root_modification_time)
        event = OLECFDocumentSummaryInformationEvent(
            date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)


class SummaryInformationOLECFPlugin(interface.OLECFPlugin):
  """Plugin that parses the SummaryInformation item from an OLECF file."""

  NAME = 'olecf_summary'
  DESCRIPTION = 'Parser for a SummaryInformation OLECF stream.'

  # pylint: disable=anomalous-backslash-in-string
  REQUIRED_ITEMS = frozenset(['\005SummaryInformation'])

  _DATE_TIME_DESCRIPTIONS = {
      'creation_time': 'Document Creation Time',
      'last_printed_time': 'Document Last Printed Time',
      'last_save_time': 'Document Last Save Time',
  }

  def Process(self, parser_mediator, root_item=None, **kwargs):
    """Parses a summary information OLECF item.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      root_item (Optional[pyolecf.item]): root item of the OLECF file.

    Raises:
      ValueError: If the root item is not set.
    """
    # This will raise if unhandled keyword arguments are passed.
    super(SummaryInformationOLECFPlugin, self).Process(
        parser_mediator, **kwargs)

    if not root_item:
      raise ValueError('Root item not set.')

    root_creation_time, root_modification_time = self._GetTimestamps(root_item)

    for item_name in self.REQUIRED_ITEMS:
      item = root_item.get_sub_item_by_name(item_name)
      if not item:
        continue

      summary_information = OLECFSummaryInformation(item)
      event_data = summary_information.GetEventData(
          data_type='olecf:summary_info')
      event_data.name = 'Summary Information'

      for property_name, date_time in iter(
          summary_information.date_time_properties.items()):
        date_time_description = self._DATE_TIME_DESCRIPTIONS.get(
            property_name, definitions.TIME_DESCRIPTION_UNKNOWN)
        event = OLECFSummaryInformationEvent(date_time, date_time_description)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      if root_creation_time:
        date_time = dfdatetime_filetime.Filetime(
            timestamp=root_creation_time)
        event = OLECFSummaryInformationEvent(
            date_time, definitions.TIME_DESCRIPTION_CREATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)

      if root_modification_time:
        date_time = dfdatetime_filetime.Filetime(
            timestamp=root_modification_time)
        event = OLECFSummaryInformationEvent(
            date_time, definitions.TIME_DESCRIPTION_MODIFICATION)
        parser_mediator.ProduceEventWithEventData(event, event_data)


olecf.OLECFParser.RegisterPlugins([
    DocumentSummaryInformationOLECFPlugin, SummaryInformationOLECFPlugin])
