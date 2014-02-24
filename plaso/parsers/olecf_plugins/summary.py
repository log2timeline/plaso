#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""Plugin to parse the OLECF summary/document summary information items."""

from plaso.lib import event

from plaso.parsers.olecf_plugins import interface


# TODO: Move some of the functions here to a higher level (to the interface)
# so the these functions can be shared by other plugins.
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
    self.name = u'Summary Information'

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
    self.name = u'Document Summary Information'

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


class DocumentSummaryPlugin(interface.OlecfPlugin):
  """Plugin that parses DocumentSummary information from an OLECF file."""

  NAME = 'olecf_document_summary'

  REQUIRED_ITEMS = frozenset(['\005DocumentSummaryInformation'])

  def GetEntries(self, root_item, items, **unused_kwargs):
    """Generate event containers based on the document summary item."""
    for item in items:
      event_container = OleCfDocumentSummaryInfoEventContainer(item)
      self.FillContainer(event_container, root_item)

      yield event_container


class SummaryInfoPlugin(interface.OlecfPlugin):
  """Plugin that parses the SummaryInformation item from an OLECF file."""

  NAME = 'olecf_summary'

  REQUIRED_ITEMS = frozenset(['\005SummaryInformation'])

  def GetEntries(self, root_item, items, **unused_kwargs):
    """Generate event containers based on the summary information item."""
    for item in items:
      event_container = OleCfSummaryInfoEventContainer(item)
      self.FillContainer(event_container, root_item)

      yield event_container
