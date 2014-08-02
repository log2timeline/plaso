#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the 'License');
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
"""Parser for Java Cache IDX files."""

# TODO:
#  * 6.02 files did not retain IP addresses. However, the
#    deploy_resource_codebase header field may contain the host IP.
#    This needs to be researched further, as that field may not always
#    be present. 6.02 files will currently return 'Unknown'.
import construct

from plaso.events import time_events
from plaso.lib import errors
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import interface


class JavaIDXEvent(time_events.TimestampEvent):
  """Convenience class for a Java IDX cache file download event."""

  DATA_TYPE = 'java:download:idx'

  def __init__(
      self, timestamp, timestamp_description, idx_version, url, ip_address):
    """Initializes the event object.

    Args:
      timestamp: The timestamp value.
      timestamp_description: The description of the usage of the time value.
      idx_version: Version of IDX file.
      url: URL of the downloaded file.
      ip_address: IP address of the host in the URL.
    """
    super(JavaIDXEvent, self).__init__(timestamp, timestamp_description)
    self.idx_version = idx_version
    self.url = url
    self.ip_address = ip_address


class JavaIDXParser(interface.BaseParser):
  """Parse Java IDX files for download events.

  There are five structures defined. 6.02 files had one generic section
  that retained all data. From 6.03, the file went to a multi-section
  format where later sections were optional and had variable-lengths.
  6.03, 6.04, and 6.05 files all have their main data section (#2)
  begin at offset 128. The short structure is because 6.05 files
  deviate after the 8th byte. So, grab the first 8 bytes to ensure it's
  valid, get the file version, then continue on with the correct
  structures.
  """

  NAME = 'java_idx'

  IDX_SHORT_STRUCT = construct.Struct(
      'magic',
      construct.UBInt8('busy'),
      construct.UBInt8('incomplete'),
      construct.UBInt32('idx_version'))

  IDX_602_STRUCT = construct.Struct(
      'IDX_602_Full',
      construct.UBInt16('null_space'),
      construct.UBInt8('shortcut'),
      construct.UBInt32('content_length'),
      construct.UBInt64('last_modified_date'),
      construct.UBInt64('expiration_date'),
      construct.PascalString(
          'version_string', length_field=construct.UBInt16('length')),
      construct.PascalString(
          'url', length_field=construct.UBInt16('length')),
      construct.PascalString(
          'namespace', length_field=construct.UBInt16('length')),
      construct.UBInt32('FieldCount'))

  IDX_605_SECTION_ONE_STRUCT = construct.Struct(
      'IDX_605_Section1',
      construct.UBInt8('shortcut'),
      construct.UBInt32('content_length'),
      construct.UBInt64('last_modified_date'),
      construct.UBInt64('expiration_date'),
      construct.UBInt64('validation_date'),
      construct.UBInt8('signed'),
      construct.UBInt32('sec2len'),
      construct.UBInt32('sec3len'),
      construct.UBInt32('sec4len'))

  IDX_605_SECTION_TWO_STRUCT = construct.Struct(
      'IDX_605_Section2',
      construct.PascalString(
          'version', length_field=construct.UBInt16('length')),
      construct.PascalString(
          'url', length_field=construct.UBInt16('length')),
      construct.PascalString(
          'namespec', length_field=construct.UBInt16('length')),
      construct.PascalString(
          'ip_address', length_field=construct.UBInt16('length')),
      construct.UBInt32('FieldCount'))

  # Java uses Pascal-style strings, but with a 2-byte length field.
  JAVA_READUTF_STRING = construct.Struct(
      'Java.ReadUTF',
      construct.PascalString(
          'string', length_field=construct.UBInt16('length')))

  def Parse(self, file_entry):
    """Extract data from a Java cache IDX file.

    This is the main parsing engine for the parser. It determines if
    the selected file is a proper IDX file. It then checks the file
    version to determine the correct structure to apply to extract
    data.

    Args:
      file_entry: A file entry object.

    Yields:
      An EventObject (JavaIDXEvent) that contains the extracted attributes.
    """
    file_object = file_entry.GetFileObject()
    try:
      magic = self.IDX_SHORT_STRUCT.parse_stream(file_object)
    except (IOError, construct.FieldError) as exception:
      raise errors.UnableToParseFile(
          u'Unable to parse Java IDX file with error: {0:s}.'.format(exception))

    # Fields magic.busy and magic.incomplete are normally 0x00. They
    # are set to 0x01 if the file is currently being downloaded. Logic
    # checks for > 1 to avoid a race condition and still reject any
    # file with other data.
    # Field magic.idx_version is the file version, of which only
    # certain versions are supported.
    if magic.busy > 1 or magic.incomplete > 1:
      raise errors.UnableToParseFile(u'Not a valid Java IDX file')

    if not magic.idx_version in [602, 603, 604, 605]:
      raise errors.UnableToParseFile(u'Not a valid Java IDX file')

    # Obtain the relevant values from the file. The last modified date
    # denotes when the file was last modified on the HOST. For example,
    # when the file was uploaded to a web server.
    if magic.idx_version == 602:
      section_one = self.IDX_602_STRUCT.parse_stream(file_object)
      last_modified_date = section_one.last_modified_date
      url = section_one.url
      ip_address = 'Unknown'
      http_header_count = section_one.FieldCount
    elif magic.idx_version in [603, 604, 605]:

      # IDX 6.03 and 6.04 have two unused bytes before the structure.
      if magic.idx_version in [603, 604]:
        file_object.read(2)

      # IDX 6.03, 6.04, and 6.05 files use the same structures for the
      # remaining data.
      section_one = self.IDX_605_SECTION_ONE_STRUCT.parse_stream(file_object)
      last_modified_date = section_one.last_modified_date
      if file_object.get_size() > 128:
        file_object.seek(128)  # Static offset for section 2.
        section_two = self.IDX_605_SECTION_TWO_STRUCT.parse_stream(file_object)
        url = section_two.url
        ip_address = section_two.ip_address
        http_header_count = section_two.FieldCount
      else:
        url = 'Unknown'
        ip_address = 'Unknown'
        http_header_count = 0

    # File offset is now just prior to HTTP headers. Make sure there
    # are headers, and then parse them to retrieve the download date.
    download_date = None
    for field in range(0, http_header_count):
      field = self.JAVA_READUTF_STRING.parse_stream(file_object)
      value = self.JAVA_READUTF_STRING.parse_stream(file_object)
      if field.string == 'date':
        # Time string "should" be in UTC or have an associated time zone
        # information in the string itself. If that is not the case then
        # there is no reliable method for plaso to determine the proper
        # timezone, so the assumption is that it is UTC.
        download_date = timelib.Timestamp.FromTimeString(
            value.string, gmt_as_timezone=False)

    if not url or not ip_address:
      raise errors.UnableToParseFile(
          u'Unexpected Error: URL or IP address not found in file.')

    last_modified_timestamp = timelib.Timestamp.FromJavaTime(
        last_modified_date)
    # TODO: Move the timestamp description fields into eventdata.
    yield JavaIDXEvent(
        last_modified_timestamp, 'File Hosted Date', magic.idx_version, url,
        ip_address)

    if section_one:
      expiration_date = section_one.get('expiration_date', None)
      if expiration_date:
        expiration_timestamp = timelib.Timestamp.FromJavaTime(expiration_date)
        yield JavaIDXEvent(
            expiration_timestamp, 'File Expiration Date', magic.idx_version,
            url, ip_address)

    if download_date:
      yield JavaIDXEvent(
          download_date, eventdata.EventTimestamp.FILE_DOWNLOADED,
          magic.idx_version, url, ip_address)
