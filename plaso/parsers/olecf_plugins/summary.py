# -*- coding: utf-8 -*-
"""Plugin to parse the OLECF summary/document summary information items."""

from dfdatetime import filetime as dfdatetime_filetime

import pyolecf

from plaso.containers import events
from plaso.parsers import olecf
from plaso.parsers.olecf_plugins import interface


class OLECFDocumentSummaryInformationEventData(events.EventData):
  """OLECF document summary information event data.

  Attributes:
    application_version (str): application version.
    category (str): category of the document, such as memo or proposal.
    codepage (str): codepage of the document summary information.
    company (str): name of the company of the document.
    content_status (str): content status.
    content_type (str): content type.
    document_parts (list[str]): names of document parts.
    document_version (int): Version of the document.
    item_creation_time (dfdatetime.DateTimeValues): creation date and time of
        the item.
    item_modification_time (dfdatetime.DateTimeValues): modification date and
        time of the item.
    language (str): Language of the document.
    links_up_to_date (bool): True if the links are up to date.
    manager (str): name of the manager of the document.
    number_of_bytes (int): size of the document in bytes.
    number_of_characters_with_white_space (int): number of characters including
        spaces in the document.
    number_of_clips (int): number of multi-media clips in the document.
    number_of_hidden_slides (int): number of hidden slides in the document.
    number_of_lines (int): number of lines in the document.
    number_of_notes (int): number of notes in the document.
    number_of_paragraphs (int): number of paragraphs in the document.
    number_of_slides (int): number of slides in the document.
    presentation_format (str): target format for presentation, such as 35mm,
        printer or video.
    scale (bool): True if scaling of the thumbnail is desired or false if
        cropping is desired.
    shared_document (bool): True if the document is shared.
  """

  DATA_TYPE = 'olecf:document_summary_info'

  def __init__(self):
    """Initializes event data."""
    super(OLECFDocumentSummaryInformationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.application_version = None
    self.category = None
    self.codepage = None
    self.company = None
    self.content_status = None
    self.content_type = None
    self.document_parts = None
    self.document_version = None
    self.item_creation_time = None
    self.item_modification_time = None
    self.language = None
    self.links_up_to_date = None
    self.manager = None
    self.number_of_bytes = None
    self.number_of_characters_with_white_space = None
    self.number_of_clips = None
    self.number_of_hidden_slides = None
    self.number_of_lines = None
    self.number_of_notes = None
    self.number_of_paragraphs = None
    self.number_of_slides = None
    self.presentation_format = None
    self.scale = None
    self.shared_document = None


class OLECFSummaryInformationEventData(events.EventData):
  """OLECF summary information event data.

  Attributes:
    application (str): name of application that created document.
    author (str): author of the document.
    codepage (str): codepage of the summary information.
    comments (str): comments.
    creation_time (dfdatetime.DateTimeValues): creation date and time of
        the document.
    edit_duration (int): total editing time.
    item_creation_time (dfdatetime.DateTimeValues): creation date and time of
        the item.
    item_modification_time (dfdatetime.DateTimeValues): modification date and
        time of the item.
    keywords (str): keywords.
    last_printed_time (dfdatetime.DateTimeValues): date and time the document
        was last printed.
    last_saved_by (str): name of user that last saved the document.
    last_save_time (dfdatetime.DateTimeValues): date and time the document was
        last saved.
    number_of_characters (int): number of characters without spaces in
        the document.
    number_of_pages (int): number of pages in the document.
    number_of_words (int): number of words in the document.
    revision_number (int): revision number.
    security_flags (int): security flags.
    subject (str): subject.
    template (str): name of the template used to created the document.
    title (str): title of the document.
  """

  DATA_TYPE = 'olecf:summary_info'

  def __init__(self):
    """Initializes event data."""
    super(OLECFSummaryInformationEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.application = None
    self.author = None
    self.codepage = None
    self.comments = None
    self.creation_time = None
    self.edit_duration = None
    self.item_creation_time = None
    self.item_modification_time = None
    self.keywords = None
    self.last_printed_time = None
    self.last_saved_by = None
    self.last_save_time = None
    self.number_of_characters = None
    self.number_of_pages = None
    self.number_of_words = None
    self.revision_number = None
    self.security_flags = None
    self.subject = None
    self.template = None
    self.title = None


class OLECFPropertySetStream(object):
  """OLECF property set stream.

  Attributes:
    date_time_properties (dict[str, dfdatetime.DateTimeValues]): date and time
        properties and values.
  """
  _CLASS_IDENTIFIER = None

  _INTEGER_TYPES = frozenset([
      pyolecf.value_types.INTEGER_16BIT_SIGNED,
      pyolecf.value_types.INTEGER_32BIT_SIGNED])

  _STRING_TYPES = frozenset([
      pyolecf.value_types.STRING_ASCII,
      pyolecf.value_types.STRING_UNICODE])

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

    if olecf_item:
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

    if property_value.type == pyolecf.value_types.FILETIME:
      filetime = property_value.data_as_integer
      if not filetime:
        return None

      return dfdatetime_filetime.Filetime(timestamp=filetime)

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

        properties_dict = self._properties

        if property_name not in properties_dict:
          properties_dict[property_name] = value

  def SetEventData(self, event_data):
    """Sets the properties as event data.

    Args:
      event_data (EventData): event data.
    """
    for property_name, property_value in self._properties.items():
      if isinstance(property_value, bytes):
        property_value = repr(property_value)
      setattr(event_data, property_name, property_value)


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
      # 0x000c: 'heading_pair',  # PIDDSI_HEADINGPAIR
      0x000d: 'document_parts',  # PIDDSI_DOCPARTS
      0x000e: 'manager',  # PIDDSI_MANAGER
      0x000f: 'company',  # PIDDSI_COMPANY
      0x0010: 'links_up_to_date',  # PIDDSI_LINKSDIRTY
      0x0011: 'number_of_characters_with_white_space',  # PIDDSI_CCHWITHSPACES
      0x0013: 'shared_document',  # PIDDSI_SHAREDDOC
      0x0017: 'application_version',  # PIDDSI_VERSION
      0x001a: 'content_type',  # PIDDSI_CONTENTTYPE
      0x001b: 'content_status',  # PIDDSI_CONTENTSTATUS
      0x001c: 'language',  # PIDDSI_LANGUAGE
      0x001d: 'document_version'}  # PIDDSI_DOCVERSION

  _PROPERTY_VALUE_MAPPINGS = {
      'application_version': '_FormatApplicationVersion'}

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
      0x000a: 'edit_duration',  # PIDSI_EDITTIME
      0x000b: 'last_printed_time',  # PIDSI_LASTPRINTED
      0x000c: 'creation_time',  # PIDSI_CREATE_DTM
      0x000d: 'last_save_time',  # PIDSI_LASTSAVE_DTM
      0x000e: 'number_of_pages',  # PIDSI_PAGECOUNT
      0x000f: 'number_of_words',  # PIDSI_WORDCOUNT
      0x0010: 'number_of_characters',  # PIDSI_CHARCOUNT
      # 0x0011: 'thumbnail',  # PIDSI_THUMBNAIL
      0x0012: 'application',  # PIDSI_APPNAME
      0x0013: 'security_flags'}  # PIDSI_SECURITY


class DocumentSummaryInformationOLECFPlugin(interface.OLECFPlugin):
  """Plugin that parses DocumentSummaryInformation item from an OLECF file."""

  NAME = 'olecf_document_summary'
  DATA_FORMAT = (
      'Document summary information (\\0x05DocumentSummaryInformation)')

  # pylint: disable=anomalous-backslash-in-string
  REQUIRED_ITEMS = frozenset(['\005DocumentSummaryInformation'])

  def Process(self, parser_mediator, root_item=None, **kwargs):
    """Extracts events from a document summary information OLECF item.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      root_item (Optional[pyolecf.item]): root item of the OLECF file.

    Raises:
      ValueError: If the root item is not set.
    """
    # This will raise if unhandled keyword arguments are passed.
    super(DocumentSummaryInformationOLECFPlugin, self).Process(
        parser_mediator, **kwargs)

    if not root_item:
      raise ValueError('Root item not set.')

    for item_name in self.REQUIRED_ITEMS:
      item = root_item.get_sub_item_by_name(item_name)
      if item:
        event_data = OLECFDocumentSummaryInformationEventData()
        event_data.item_creation_time = self._GetCreationTime(root_item)
        event_data.item_modification_time = self._GetModificationTime(root_item)

        summary_information = OLECFDocumentSummaryInformation(item)
        summary_information.SetEventData(event_data)

        parser_mediator.ProduceEventData(event_data)


class SummaryInformationOLECFPlugin(interface.OLECFPlugin):
  """Plugin that parses the SummaryInformation item from an OLECF file."""

  NAME = 'olecf_summary'
  DATA_FORMAT = (
      'Summary information (\\0x05SummaryInformation) (top-level only)')

  # pylint: disable=anomalous-backslash-in-string
  REQUIRED_ITEMS = frozenset(['\005SummaryInformation'])

  def Process(self, parser_mediator, root_item=None, **kwargs):
    """Extracts events from a summary information OLECF item.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      root_item (Optional[pyolecf.item]): root item of the OLECF file.

    Raises:
      ValueError: If the root item is not set.
    """
    # This will raise if unhandled keyword arguments are passed.
    super(SummaryInformationOLECFPlugin, self).Process(
        parser_mediator, **kwargs)

    if not root_item:
      raise ValueError('Root item not set.')

    for item_name in self.REQUIRED_ITEMS:
      item = root_item.get_sub_item_by_name(item_name)
      if item:
        event_data = OLECFSummaryInformationEventData()
        event_data.item_creation_time = self._GetCreationTime(root_item)
        event_data.item_modification_time = self._GetModificationTime(root_item)

        summary_information = OLECFSummaryInformation(item)
        summary_information.SetEventData(event_data)

        parser_mediator.ProduceEventData(event_data)


olecf.OLECFParser.RegisterPlugins([
    DocumentSummaryInformationOLECFPlugin, SummaryInformationOLECFPlugin])
