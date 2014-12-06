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
"""The CUPS IPP Control Files Parser.

CUPS IPP version 1.0:
* http://tools.ietf.org/html/rfc2565
* http://tools.ietf.org/html/rfc2566
* http://tools.ietf.org/html/rfc2567
* http://tools.ietf.org/html/rfc2568
* http://tools.ietf.org/html/rfc2569
* http://tools.ietf.org/html/rfc2639

CUPS IPP version 1.1:
* http://tools.ietf.org/html/rfc2910
* http://tools.ietf.org/html/rfc2911
* http://tools.ietf.org/html/rfc3196
* http://tools.ietf.org/html/rfc3510

CUPS IPP version 2.0:
* N/A
"""

import construct
import logging
import os

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import interface
from plaso.parsers import manager


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


# TODO: RFC Pendings types: resolution, dateTime, rangeOfInteger.
#       "dateTime" is not used by Mac OS, instead it uses integer types.
# TODO: Only tested against CUPS IPP Mac OS X.


class CupsIppEvent(event.EventObject):
  """Convenience class for an cups ipp event."""

  DATA_TYPE = 'cups:ipp:event'

  def __init__(
      self, timestamp, timestamp_desc, data_dict):
    """Initializes the event object.

    Args:
      timestamp: Timestamp of the entry.
      timestamp_desc: Description of the timestamp.
      data_dict: Dictionary with all the pairs coming from IPP file.
        user: String with the system user name.
        owner: String with the real name of the user.
        computer_name: String with the name of the computer.
        printer_id: String with the identification name of the print.
        uri: String with the URL of the CUPS service.
        job_id: String with the identification id of the job.
        job_name: String with the job name.
        copies: Integer with the number of copies.
        application: String with the application that prints the document.
        doc_usingtype: String with the type of document.
        data_dict: Dictionary with all the parsed data comming from the file.
    """
    super(CupsIppEvent, self).__init__()
    self.timestamp = timelib.Timestamp.FromPosixTime(timestamp)
    self.timestamp_desc = timestamp_desc
    # TODO: Find a better solution than to have join for each attribute.
    self.user = self._ListToString(data_dict.get('user', None))
    self.owner = self._ListToString(data_dict.get('owner', None))
    self.computer_name = self._ListToString(data_dict.get(
        'computer_name', None))
    self.printer_id = self._ListToString(data_dict.get('printer_id', None))
    self.uri = self._ListToString(data_dict.get('uri', None))
    self.job_id = self._ListToString(data_dict.get('job_id', None))
    self.job_name = self._ListToString(data_dict.get('job_name', None))
    self.copies = data_dict.get('copies', 0)[0]
    self.application = self._ListToString(data_dict.get('application', None))
    self.doc_type = self._ListToString(data_dict.get('doc_type', None))
    self.data_dict = data_dict

  def _ListToString(self, values):
    """Returns a string from a list value using comma as a delimiter.

    If any value inside the list contains comma, which is the delimiter,
    the entire field is surrounded with double quotes.

    Args:
      values: A list or tuple containing the values.

    Returns:
      A string containing all the values joined using comma as a delimiter
      or None.
    """
    if values is None:
      return

    if type(values) not in (list, tuple):
      return

    for index, value in enumerate(values):
      if ',' in value:
        values[index] = u'"{0:s}"'.format(value)

    try:
      return u', '.join(values)
    except UnicodeDecodeError as exception:
      logging.error(
          u'Unable to parse log line, with error: {0:s}'.format(exception))


class CupsIppParser(interface.BaseParser):
  """Parser for CUPS IPP files. """

  NAME = 'cups_ipp'
  DESCRIPTION = u'Parser for CUPS IPP files.'

  # INFO:
  # For each file, we have only one document with three different timestamps:
  # Created, process and finished.
  # Format:
  # [HEADER: MAGIC + KNOWN_TYPE][GROUP A]...[GROUP Z][GROUP_END: 0x03]
  # GROUP: [GROUP ID][PAIR A]...[PAIR Z] where [PAIR: NAME + VALUE]
  #   GROUP ID: [1byte ID]
  #   PAIR: [TagID][\x00][Name][Value])
  #     TagID: 1 byte integer with the type of "Value".
  #     Name: [Length][Text][\00]
  #       Name can be empty when the name has more than one value.
  #       Example: family name "lopez mata" with more than one surname.
  #       Type_Text + [0x06, family, 0x00] + [0x05, lopez, 0x00] +
  #       Type_Text + [0x00, 0x00] + [0x04, mata, 0x00]
  #     Value: can be integer, boolean, or text provided by TagID.
  #       If boolean, Value: [\x01][0x00(False)] or [\x01(True)]
  #       If integer, Value: [\x04][Integer]
  #       If text,    Value: [Length text][Text][\00]

  # Magic number that identify the CUPS IPP supported version.
  IPP_MAJOR_VERSION = 2
  IPP_MINOR_VERSION = 0
  # Supported Operation ID.
  IPP_OP_ID = 5

  # CUPS IPP File header.
  CUPS_IPP_HEADER = construct.Struct(
      'cups_ipp_header_struct',
      construct.UBInt8('major_version'),
      construct.UBInt8('minor_version'),
      construct.UBInt16('operation_id'),
      construct.UBInt32('request_id'))

  # Group ID that indicates the end of the IPP Control file.
  GROUP_END = 3
  # Identification Groups.
  GROUP_LIST = [1, 2, 4, 5, 6, 7]

  # Type ID.
  TYPE_GENERAL_INTEGER = 32
  TYPE_INTEGER = 33
  TYPE_ENUMERATION = 35
  TYPE_BOOL = 34

  # Type of values that can be extracted.
  INTEGER_8 = construct.UBInt8('integer')
  INTEGER_32 = construct.UBInt32('integer')
  TEXT = construct.PascalString(
      'text',
      length_field=construct.UBInt8('length'))
  BOOLEAN = construct.Struct(
      'boolean_value',
      construct.Padding(1),
      INTEGER_8)
  INTEGER = construct.Struct(
      'integer_value',
      construct.Padding(1),
      INTEGER_32)

  # Name of the pair.
  PAIR_NAME = construct.Struct(
      'pair_name',
      TEXT,
      construct.Padding(1))

  # Specific CUPS IPP to generic name.
  NAME_PAIR_TRANSLATION = {
      'printer-uri': u'uri',
      'job-uuid': u'job_id',
      'DestinationPrinterID': u'printer_id',
      'job-originating-user-name': u'user',
      'job-name': u'job_name',
      'document-format': u'doc_type',
      'job-originating-host-name': u'computer_name',
      'com.apple.print.JobInfo.PMApplicationName': u'application',
      'com.apple.print.JobInfo.PMJobOwner': u'owner'}

  def Parse(self, parser_context, file_entry, parser_chain=None):
    """Extract a entry from an CUPS IPP file.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
      parser_chain: Optional string containing the parsing chain up to this
                    point. The default is None.
    """
    parser_chain = self._BuildParserChain(parser_chain)

    file_object = file_entry.GetFileObject()
    file_object.seek(0, os.SEEK_SET)

    try:
      header = self.CUPS_IPP_HEADER.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      file_object.close()
      raise errors.UnableToParseFile(
          u'Unable to parse CUPS IPP Header with error: {0:s}'.format(
              exception))

    if (header.major_version != self.IPP_MAJOR_VERSION or
        header.minor_version != self.IPP_MINOR_VERSION):
      file_object.close()
      raise errors.UnableToParseFile(
          u'[{0:s}] Unsupported version number.'.format(self.NAME))

    if header.operation_id != self.IPP_OP_ID:
      # Warn if the operation ID differs from the standard one. We should be
      # able to parse the file nonetheless.
      logging.debug(
          u'[{0:s}] Unsupported operation identifier in file: {1:s}.'.format(
              self.NAME, parser_context.GetDisplayName(file_entry)))

    # Read the pairs extracting the name and the value.
    data_dict = {}
    name, value = self.ReadPair(parser_context, file_entry, file_object)
    while name or value:
      # Translate the known "name" CUPS IPP to a generic name value.
      pretty_name = self.NAME_PAIR_TRANSLATION.get(name, name)
      data_dict.setdefault(pretty_name, []).append(value)
      name, value = self.ReadPair(parser_context, file_entry, file_object)

    if u'time-at-creation' in data_dict:
      event_object = CupsIppEvent(
          data_dict['time-at-creation'][0],
          eventdata.EventTimestamp.CREATION_TIME, data_dict)
      parser_context.ProduceEvent(
          event_object, parser_chain=parser_chain, file_entry=file_entry)

    if u'time-at-processing' in data_dict:
      event_object = CupsIppEvent(
          data_dict['time-at-processing'][0],
          eventdata.EventTimestamp.START_TIME, data_dict)
      parser_context.ProduceEvent(
          event_object, parser_chain=parser_chain, file_entry=file_entry)

    if u'time-at-completed' in data_dict:
      event_object = CupsIppEvent(
          data_dict['time-at-completed'][0],
          eventdata.EventTimestamp.END_TIME, data_dict)
      parser_context.ProduceEvent(
          event_object, parser_chain=parser_chain, file_entry=file_entry)

    file_object.close()

  def ReadPair(self, parser_context, file_entry, file_object):
    """Reads an attribute name and value pair from a CUPS IPP event.

    Args:
      parser_context: A parser context object (instance of ParserContext).
      file_entry: A file entry object (instance of dfvfs.FileEntry).
      file_object: a file-like object that points to a file.

    Returns:
      A list of name and value. If name and value cannot be read both are
      set to None.
    """
    # Pair = Type ID + Name + Value.
    try:
      # Can be:
      #   Group ID + IDtag = Group ID (1byte) + Tag ID (1byte) + '0x00'.
      #   IDtag = Tag ID (1byte) + '0x00'.
      type_id = self.INTEGER_8.parse_stream(file_object)
      if type_id == self.GROUP_END:
        return None, None

      elif type_id in self.GROUP_LIST:
        # If it is a group ID we must read the next byte that contains
        # the first TagID.
        type_id = self.INTEGER_8.parse_stream(file_object)

      # 0x00 separator character.
      _ = self.INTEGER_8.parse_stream(file_object)

    except (IOError, construct.FieldError):
      logging.warning(
          u'[{0:s}] Unsupported identifier in file: {1:s}.'.format(
              self.NAME, parser_context.GetDisplayName(file_entry)))
      return None, None

    # Name = Length name + name + 0x00
    try:
      name = self.PAIR_NAME.parse_stream(file_object).text
    except (IOError, construct.FieldError):
      logging.warning(
          u'[{0:s}] Unsupported name in file: {1:s}.'.format(
              self.NAME, parser_context.GetDisplayName(file_entry)))
      return None, None

    # Value: can be integer, boolean or text select by Type ID.
    try:
      if type_id in [
          self.TYPE_GENERAL_INTEGER, self.TYPE_INTEGER, self.TYPE_ENUMERATION]:
        value = self.INTEGER.parse_stream(file_object).integer

      elif type_id == self.TYPE_BOOL:
        value = bool(self.BOOLEAN.parse_stream(file_object).integer)

      else:
        value = self.TEXT.parse_stream(file_object)

    except (IOError, construct.FieldError):
      logging.warning(
          u'[{0:s}] Unsupported value in file: {1:s}.'.format(
              self.NAME, parser_context.GetDisplayName(file_entry)))
      return None, None

    return name, value


manager.ParsersManager.RegisterParser(CupsIppParser)
