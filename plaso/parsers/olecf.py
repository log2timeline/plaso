#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Parser for OLE Compound Files (OLECF)."""

import logging

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser

import pyolecf


# TODO: note that this parser will be changed to act as a generic parser
# for various types of OLECF based file formats.


if pyolecf.get_version() < '20131012':
  raise ImportWarning('OleCfParser requires at least pyolecf 20131012.')


class OleDefinitions(object):
  """Convenience class for OLE definitions."""

  VT_I2 = 0x0002
  VT_I4 = 0x0003
  VT_BOOL = 0x000b
  VT_LPSTR = 0x001e
  VT_LPWSTR = 0x001e
  VT_FILETIME = 0x0040
  VT_CF = 0x0047


class OleCfItemEventContainer(event.EventContainer):
  """Convenience class for an OLECF item event container."""

  def __init__(self, olecf_item):
    """Initializes the event container.

    Args:
      olecf_item: The OLECF item (pyolecf.item).
    """
    super(OleCfItemEventContainer, self).__init__()

    self.data_type = 'olecf:item'

    # TODO: need a better way to express the original location of the
    # original data.
    self.offset = 0

    self.name = olecf_item.name
    # TODO: have pyolecf return the item type here.
    # self.type = olecf_item.type
    self.size = olecf_item.size


class OleCfSummaryInfoEventContainer(event.EventContainer):
  """Convenience class for an OLECF Summary info event container."""
  _CLASS_IDENTIFIER = 'f29f85e0-4ff9-1068-ab91-08002b27b3d9'

  _PROPERTY_NAMES_INT32 = {
      0x000e: 'number_of_pages',  # PIDSI_PAGECOUNT
      0x000f: 'number_of_words',  # PIDSI_WORDCOUNT
      0x0010: 'number_of_characters',  # PIDSI_CHARCOUNT
      0x0013: 'security',  # PIDSI_SECURITY
  }

  _PROPERTY_NAMES_STRING = {
      0x0002: 'title',  # PIDSI_TITLE
      0x0003: 'subject',  # PIDSI_SUBJECT
      0x0004: 'author',  # PIDSI_AUTHOR
      0x0005: 'keywords',  # PIDSI_KEYWORDS
      0x0006: 'comments',  # PIDSI_COMMENTS
      0x0007: 'template',  # PIDSI_TEMPLATE
      0x0008: 'last_saved_by',  # PIDSI_LASTAUTHOR
      0x0009: 'revision_number',  # PIDSI_REVNUMBER
      0x0012: 'application',  # PIDSI_APPNAME
  }

  PIDSI_CODEPAGE = 0x0001
  PIDSI_EDITTIME = 0x000a
  PIDSI_LASTPRINTED = 0x000b
  PIDSI_CREATE_DTM = 0x000c
  PIDSI_LASTSAVE_DTM = 0x000d
  PIDSI_THUMBNAIL = 0x0011

  def __init__(self, olecf_item):
    """Initializes the event container.

    Args:
      olecf_item: The OLECF item (pyolecf.property_set_stream).
    """
    super(OleCfSummaryInfoEventContainer, self).__init__()

    self.data_type = 'olecf:summary_info'

    # TODO: make this more elegant/generic also in light of OLECF
    # sub parsers (plugins).
    self._InitFromPropertySet(olecf_item.set)

  def _InitFromPropertySet(self, property_set):
    """Initializes the event container from a property set.

    Args:
      property_set: The OLECF property set (pyolecf.property_set).
    """
    # Combine the values of multiple property sections
    # but do not override properties that are already set.
    for property_section in property_set.sections:
      self._InitFromPropertySection(property_section)

  def _InitFromPropertySection(self, property_section):
    """Initializes the event container from a property section.

    Args:
      property_section: The OLECF property section (pyolecf.property_section).
    """
    if property_section.class_identifier == self._CLASS_IDENTIFIER:
      for property_value in property_section.properties:
        self._InitFromPropertyValue(property_value)

  def _InitFromPropertyValue(self, property_value):
    """Initializes the event container from a property value.

    Args:
      property_value: The OLECF property value (pyolecf.property_value).
    """
    if property_value.type == OleDefinitions.VT_I2:
      self._InitFromPropertyValueTypeInt16(property_value)

    elif property_value.type == OleDefinitions.VT_I4:
      self._InitFromPropertyValueTypeInt32(property_value)

    elif (property_value.type == OleDefinitions.VT_LPSTR or
          property_value.type == OleDefinitions.VT_LPWSTR):
      self._InitFromPropertyValueTypeString(property_value)

    elif property_value.type == OleDefinitions.VT_FILETIME:
      self._InitFromPropertyValueTypeFiletime(property_value)

  def _InitFromPropertyValueTypeInt16(self, property_value):
    """Initializes the event container from a 16-bit int type property value.

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
    """Initializes the event container from a 32-bit int type property value.

    Args:
      property_value: The OLECF property value (pyolecf.property_value
                      of type VT_I4).
    """
    property_name = self._PROPERTY_NAMES_INT32.get(
        property_value.identifier, None)

    if property_name and not hasattr(self.attributes, property_name):
      self.attributes[property_name] = property_value.data_as_integer

  def _InitFromPropertyValueTypeString(self, property_value):
    """Initializes the event container from a string type property value.

    Args:
      property_value: The OLECF property value (pyolecf.property_value
                      of type VT_LPSTR or VT_LPWSTR).
    """
    property_name = self._PROPERTY_NAMES_STRING.get(
        property_value.identifier, None)

    if property_name and not hasattr(self.attributes, property_name):
      self.attributes[property_name] = property_value.data_as_string

  def _InitFromPropertyValueTypeFiletime(self, property_value):
    """Initializes the event container from a filetime type property value.

    Args:
      property_value: The OLECF property value (pyolecf.property_value
                      of type VT_FILETIME).
    """
    if property_value.identifier == self.PIDSI_LASTPRINTED:
      self.Append(event.FiletimeEvent(
          property_value.data_as_integer,
          'Document Last Printed Time',
          self.data_type))
    elif property_value.identifier == self.PIDSI_CREATE_DTM:
      self.Append(event.FiletimeEvent(
          property_value.data_as_integer,
          'Document Creation Time',
          self.data_type))
    elif property_value.identifier == self.PIDSI_LASTSAVE_DTM:
      self.Append(event.FiletimeEvent(
          property_value.data_as_integer,
          'Document Last Save Time',
          self.data_type))
    elif property_value.identifier == self.PIDSI_EDITTIME:
      # property_name = 'total_edit_time'
      # TODO: handle duration.
      pass


class OleCfDocumentSummaryInfoEventContainer(event.EventContainer):
  """Convenience class for an OLECF Document Summary info event container."""
  _CLASS_IDENTIFIER = 'd5cdd502-2e9c-101b-9397-08002b2cf9ae'

  _PROPERTY_NAMES_BOOL = {
      0x0013: 'shared_document',  # PIDDSI_SHAREDDOC
  }

  _PROPERTY_NAMES_INT32 = {
      0x0004: 'number_of_bytes',  # PIDDSI_BYTECOUNT
      0x0005: 'number_of_lines',  # PIDDSI_LINECOUNT
      0x0006: 'number_of_paragraphs',  # PIDDSI_PARCOUNT
      0x0007: 'number_of_slides',  # PIDDSI_SLIDECOUNT
      0x0008: 'number_of_notes',  # PIDDSI_NOTECOUNT
      0x0009: 'number_of_hidden_slides',  # PIDDSI_HIDDENCOUNT
      0x000a: 'number_of_clips',  # PIDDSI_MMCLIPCOUNT
      0x0011: 'number_of_characters_with_white_space',  # PIDDSI_CCHWITHSPACES
      0x0017: 'application_version',  # PIDDSI_VERSION
  }

  _PROPERTY_NAMES_STRING = {
      0x000e: 'manager',  # PIDDSI_MANAGER
      0x000f: 'company',  # PIDDSI_COMPANY
      0x001a: 'content_type',  # PIDDSI_CONTENTTYPE
      0x001b: 'content_status',  # PIDDSI_CONTENTSTATUS
      0x001c: 'language',  # PIDDSI_LANGUAGE
      0x001d: 'document_version',  # PIDDSI_DOCVERSION
  }

  PIDDSI_CODEPAGE = 0x0001
  PIDDSI_CATEGORY = 0x0002
  PIDDSI_PRESFORMAT = 0x0003
  PIDDSI_SCALE = 0x000b
  PIDDSI_HEADINGPAIR = 0x000c
  PIDDSI_DOCPARTS = 0x000d
  PIDDSI_LINKSDIRTY = 0x0010
  PIDDSI_VERSION = 0x0017

  def __init__(self, olecf_item):
    """Initializes the event container.

    Args:
      olecf_item: The OLECF item (pyolecf.property_set_stream).
    """
    super(OleCfDocumentSummaryInfoEventContainer, self).__init__()

    self.data_type = 'olecf:document_summary_info'

    self._InitFromPropertySet(olecf_item.set)

  def _InitFromPropertySet(self, property_set):
    """Initializes the event container from a property set.

    Args:
      property_set: The OLECF property set (pyolecf.property_set).
    """
    # Combine the values of multiple property sections
    # but do not override properties that are already set.
    for property_section in property_set.sections:
      self._InitFromPropertySection(property_section)

  def _InitFromPropertySection(self, property_section):
    """Initializes the event container from a property section.

    Args:
      property_section: The OLECF property section (pyolecf.property_section).
    """
    if property_section.class_identifier == self._CLASS_IDENTIFIER:
      for property_value in property_section.properties:
        self._InitFromPropertyValue(property_value)

  def _InitFromPropertyValue(self, property_value):
    """Initializes the event container from a property value.

    Args:
      property_value: The OLECF property value (pyolecf.property_value).
    """
    if property_value.type == OleDefinitions.VT_I2:
      self._InitFromPropertyValueTypeInt16(property_value)

    elif property_value.type == OleDefinitions.VT_I4:
      self._InitFromPropertyValueTypeInt32(property_value)

    elif property_value.type == OleDefinitions.VT_BOOL:
      self._InitFromPropertyValueTypeBool(property_value)

    elif (property_value.type == OleDefinitions.VT_LPSTR or
          property_value.type == OleDefinitions.VT_LPWSTR):
      self._InitFromPropertyValueTypeString(property_value)

  def _InitFromPropertyValueTypeInt16(self, property_value):
    """Initializes the event container from a 16-bit int type property value.

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
    """Initializes the event container from a 32-bit int type property value.

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
      self.attributes[property_name] = '{0:d}.{1:d}'.format(
          application_version >> 16, application_version & 0xffff)

    elif property_name and not hasattr(self.attributes, property_name):
      self.attributes[property_name] = property_value.data_as_integer

  def _InitFromPropertyValueTypeBool(self, property_value):
    """Initializes the event container from a boolean type property value.

    Args:
      property_value: The OLECF property value (pyolecf.property_value
                      of type VT_BOOL).
    """
    property_name = self._PROPERTY_NAMES_BOOL.get(
        property_value.identifier, None)

    if property_name and not hasattr(self.attributes, property_name):
      self.attributes[property_name] = property_value.data_as_boolean

  def _InitFromPropertyValueTypeString(self, property_value):
    """Initializes the event container from a string type property value.

    Args:
      property_value: The OLECF property value (pyolecf.property_value
                      of type VT_LPSTR or VT_LPWSTR).
    """
    property_name = self._PROPERTY_NAMES_STRING.get(
        property_value.identifier, None)

    if property_name and not hasattr(self.attributes, property_name):
      self.attributes[property_name] = property_value.data_as_string


class OleCfParser(parser.PlasoParser):
  """Parses OLE Compound Files (OLECF)."""

  NAME = 'olecf'

  def __init__(self, pre_obj, config):
    """Initializes the parser.

    Args:
      pre_obj: pre-parsing object.
      config: configuration object.
    """
    super(OleCfParser, self).__init__(pre_obj, config)
    self._codepage = getattr(self._pre_obj, 'codepage', 'cp1252')

  def _ParseItem(self, olecf_item, level=0):
    """Extracts data from an OLECF item.

    Args:
      olecf_item: an OLECF item (pyolecf.item).
      level: optional level of depth (or height) of the items,
             the default is 0 (root).

    Yields:
      An event container (EventContainer) that contains the parsed
      attributes.
    """
    try:
      creation_time = olecf_item.get_creation_time_as_integer()
    except OverflowError as exception:
      logging.warning(
          u'Unable to read the creaton time, error: %s', exception)
      creation_time = 0

    try:
      modification_time = olecf_item.get_modification_time_as_integer()
    except OverflowError as exception:
      logging.warning(
          u'Unable to read the modification time, error: %s', exception)
      modification_time = 0

    # TODO: needed plug-in behaviors:
    # default: fallback, extract time stamps and name
    # single: trigger on SummaryInformation or DocumentSummaryInformation
    # pre-scan: DestList should trigger [1-9a-f][0-9a-f]* to be parsed
    #           as LNK files. Similar for MSI?

    # TODO: make sure item is a stream when passed to sub parser?
    # stream object has data and behaves like file-like object other
    # object might not.

    # TODO: for now ignore Document Summary Information and Summary Information
    # property streams outside of the root.

    # Shut up pylint
    # * W1401: Anomalous backslash in string: '\0'.
    #          String constant might be missing an r prefix.
    # pylint: disable-msg=W1401
    if level == 1 and olecf_item.name == '\005SummaryInformation':
      event_container = OleCfSummaryInfoEventContainer(olecf_item)

    # pylint: disable-msg=W1401
    elif level == 1 and olecf_item.name == '\005DocumentSummaryInformation':
      event_container = OleCfDocumentSummaryInfoEventContainer(olecf_item)

    # Do not add other items without a useful time value.
    elif creation_time != 0 or modification_time != 0:
      event_container = OleCfItemEventContainer(olecf_item)

    else:
      event_container = None

    # Need to check against None here since event container will evaluate
    # to false if it does not contain events.
    # TODO: Instead of creating new events here we need to group these
    # together and create a single Grouped Event. Since we still don't
    # have the groups implemented this is pending that implementation.
    if event_container != None:
      # If the event container does not contain any events
      # make sure to add at least one. Office template documents sometimes
      # contain a creation time of -1 (0xffffffffffffffff).
      if (creation_time not in [0, 0xffffffffffffffffL] or
          (modification_time == 0 and event_container.number_of_events == 0)):
        if creation_time == 0xffffffffffffffffL:
          creation_time = 0

        event_container.Append(event.FiletimeEvent(
            creation_time,
            eventdata.EventTimestamp.CREATION_TIME,
            event_container.data_type))

      if modification_time != 0:
        event_container.Append(event.FiletimeEvent(
            modification_time,
            eventdata.EventTimestamp.MODIFICATION_TIME,
            event_container.data_type))

      yield event_container

    for sub_item in olecf_item.sub_items:
      # Need to yield every event container individually otherwise
      # a generator object is yielded.
      for event_container in self._ParseItem(sub_item, level=(level + 1)):
        yield event_container

  def Parse(self, file_object):
    """Extracts data from an OLE Compound File (OLECF).

    Args:
      file_object: a file-like object to read data from.

    Yields:
      An event container (EventContainer) that contains the parsed
      attributes.
    """
    olecf_file = pyolecf.file()
    olecf_file.set_ascii_codepage(self._codepage)

    try:
      olecf_file.open_file_object(file_object)
    except IOError as exception:
      raise errors.UnableToParseFile('[%s] unable to parse file %s: %s' % (
          self.parser_name, file_object.name, exception))

    # Need to yield every event container individually otherwise
    # a generator object is yielded.
    for event_container in self._ParseItem(olecf_file.root_item, level=0):
      yield event_container
