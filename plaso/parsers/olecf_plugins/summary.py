# -*- coding: utf-8 -*-
"""Plugin to parse the OLECF summary/document summary information items."""

from dfdatetime import filetime as dfdatetime_filetime

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.parsers import olecf
from plaso.parsers.olecf_plugins import interface


class OLECFPropertySetStream(object):
  """OLECF property set stream.

  Attributes:
    date_time_properties (dict[str, dfdatetime.DateTimeValues]): date and time
        properties and values.
  """
  # OLE variant types.
  VT_I2 = 0x0002
  VT_I4 = 0x0003
  VT_BOOL = 0x000b
  VT_LPSTR = 0x001e
  VT_LPWSTR = 0x001e
  VT_FILETIME = 0x0040
  VT_CF = 0x0047

  _CLASS_IDENTIFIER = None

  _INTEGER_TYPES = frozenset([VT_I2, VT_I4, VT_FILETIME])
  _STRING_TYPES = frozenset([VT_LPSTR, VT_LPWSTR])

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
    if property_value.type == self.VT_BOOL:
      return property_value.data_as_boolean

    elif property_value.type in self._INTEGER_TYPES:
      return property_value.data_as_integer

    elif property_value.type in self._STRING_TYPES:
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
          property_name = u'0x{0:04}'.format(property_value.identifier)

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
      setattr(event_data, property_name, property_value)

    return event_data


class OLECFDocumentSummaryInformationEvent(time_events.DateTimeValuesEvent):
  """Convenience class for an OLECF Document summary information event.

  Attributes:
    name (str): name of the OLECF item.
  """

  DATA_TYPE = u'olecf:document_summary_info'

  def __init__(self, date_time, date_time_description):
    """Initializes an event.

    Args:
      date_time (dfdatetime.DateTimeValues): date and time values.
      date_time_description (str): description of the meaning of the date
          and time values.
    """
    super(OLECFDocumentSummaryInformationEvent, self).__init__(
        date_time, date_time_description)
    self.name = u'Document Summary Information'


class OLECFSummaryInformationEvent(time_events.DateTimeValuesEvent):
  """Convenience class for an OLECF Summary information event.

  Attributes:
    name (str): name of the OLECF item.
  """

  DATA_TYPE = u'olecf:summary_info'

  def __init__(self, date_time, date_time_description):
    """Initializes an event.

    Args:
      date_time (dfdatetime.DateTimeValues): date and time values.
      date_time_description (str): description of the meaning of the date
          and time values.
    """
    super(OLECFSummaryInformationEvent, self).__init__(
        date_time, date_time_description)
    self.name = u'Summary Information'


class OLECFDocumentSummaryInformation(OLECFPropertySetStream):
  """OLECF Document Summary information property set."""

  _CLASS_IDENTIFIER = u'd5cdd502-2e9c-101b-9397-08002b2cf9ae'

  _PROPERTY_NAMES = {
      0x0001: u'codepage',  # PIDDSI_CODEPAGE
      0x0002: u'category',  # PIDDSI_CATEGORY
      0x0003: u'presentation_format',  # PIDDSI_PRESFORMAT
      0x0004: u'number_of_bytes',  # PIDDSI_BYTECOUNT
      0x0005: u'number_of_lines',  # PIDDSI_LINECOUNT
      0x0006: u'number_of_paragraphs',  # PIDDSI_PARCOUNT
      0x0007: u'number_of_slides',  # PIDDSI_SLIDECOUNT
      0x0008: u'number_of_notes',  # PIDDSI_NOTECOUNT
      0x0009: u'number_of_hidden_slides',  # PIDDSI_HIDDENCOUNT
      0x000a: u'number_of_clips',  # PIDDSI_MMCLIPCOUNT
      0x000b: u'scale',  # PIDDSI_SCALE
      0x000c: u'heading_pair',  # PIDDSI_HEADINGPAIR
      0x000d: u'document_parts',  # PIDDSI_DOCPARTS
      0x000e: u'manager',  # PIDDSI_MANAGER
      0x000f: u'company',  # PIDDSI_COMPANY
      0x0010: u'links_dirty',  # PIDDSI_LINKSDIRTY
      0x0011: u'number_of_characters_with_white_space',  # PIDDSI_CCHWITHSPACES
      0x0013: u'shared_document',  # PIDDSI_SHAREDDOC
      0x0017: u'application_version',  # PIDDSI_VERSION
      0x001a: u'content_type',  # PIDDSI_CONTENTTYPE
      0x001b: u'content_status',  # PIDDSI_CONTENTSTATUS
      0x001c: u'language',  # PIDDSI_LANGUAGE
      0x001d: u'document_version',  # PIDDSI_DOCVERSION
  }

  _PROPERTY_VALUE_MAPPINGS = {
      u'application_version': u'_FormatApplicationVersion',
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
    return u'{0:d}.{1:d}'.format(
        application_version >> 16, application_version & 0xffff)


class OLECFSummaryInformation(OLECFPropertySetStream):
  """OLECF Summary information property set."""

  _CLASS_IDENTIFIER = u'f29f85e0-4ff9-1068-ab91-08002b27b3d9'

  _DATE_TIME_PROPERTIES = frozenset([
      u'creation_time', u'last_printed_time', u'last_save_time'])

  _PROPERTY_NAMES = {
      0x0001: u'codepage',  # PIDSI_CODEPAGE
      0x0002: u'title',  # PIDSI_TITLE
      0x0003: u'subject',  # PIDSI_SUBJECT
      0x0004: u'author',  # PIDSI_AUTHOR
      0x0005: u'keywords',  # PIDSI_KEYWORDS
      0x0006: u'comments',  # PIDSI_COMMENTS
      0x0007: u'template',  # PIDSI_TEMPLATE
      0x0008: u'last_saved_by',  # PIDSI_LASTAUTHOR
      0x0009: u'revision_number',  # PIDSI_REVNUMBER
      0x000a: u'edit_time',  # PIDSI_EDITTIME
      0x000b: u'last_printed_time',  # PIDSI_LASTPRINTED
      0x000c: u'creation_time',  # PIDSI_CREATE_DTM
      0x000d: u'last_save_time',  # PIDSI_LASTSAVE_DTM
      0x000e: u'number_of_pages',  # PIDSI_PAGECOUNT
      0x000f: u'number_of_words',  # PIDSI_WORDCOUNT
      0x0010: u'number_of_characters',  # PIDSI_CHARCOUNT
      0x0011: u'thumbnail',  # PIDSI_THUMBNAIL
      0x0012: u'application',  # PIDSI_APPNAME
      0x0013: u'security',  # PIDSI_SECURITY
  }


class DocumentSummaryInformationOLECFPlugin(interface.OLECFPlugin):
  """Plugin that parses DocumentSummaryInformation item from an OLECF file."""

  NAME = u'olecf_document_summary'
  DESCRIPTION = u'Parser for a DocumentSummaryInformation OLECF stream.'

  # pylint: disable=anomalous-backslash-in-string
  REQUIRED_ITEMS = frozenset([u'\005DocumentSummaryInformation'])

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
      raise ValueError(u'Root item not set.')

    root_creation_time, root_modification_time = self._GetTimestamps(root_item)

    for item_name in self.REQUIRED_ITEMS:
      item = root_item.get_sub_item_by_name(item_name)
      if not item:
        continue

      summary_information = OLECFDocumentSummaryInformation(item)
      event_data = summary_information.GetEventData(
          data_type=u'olecf:document_summary_info')
      event_data.name = u'Document Summary Information'

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

  NAME = u'olecf_summary'
  DESCRIPTION = u'Parser for a SummaryInformation OLECF stream.'

  # pylint: disable=anomalous-backslash-in-string
  REQUIRED_ITEMS = frozenset([u'\005SummaryInformation'])

  _DATE_TIME_DESCRIPTIONS = {
      u'creation_time': u'Document Creation Time',
      u'last_printed_time': u'Document Last Printed Time',
      u'last_save_time': u'Document Last Save Time',
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
      raise ValueError(u'Root item not set.')

    root_creation_time, root_modification_time = self._GetTimestamps(root_item)

    for item_name in self.REQUIRED_ITEMS:
      item = root_item.get_sub_item_by_name(item_name)
      if not item:
        continue

      summary_information = OLECFSummaryInformation(item)
      event_data = summary_information.GetEventData(
          data_type=u'olecf:summary_info')
      event_data.name = u'Summary Information'

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
