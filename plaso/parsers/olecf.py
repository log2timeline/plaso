#!/usr/bin/python
# -*- coding: utf-8 -*-
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
"""This file contains a parser for extracting olecf metadata."""

import datetime

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import eventdata
from plaso.lib import parser
from plaso.lib import timelib

import OleFileIO_PL

__author__ = 'David Nides (david.nides@gmail.com)'


class OLECF(parser.PlasoParser):
  """Parse metadata from OLE files."""

  DATA_TYPE = 'metadata:OLECF'

  MAGIC = '\320\317\021\340\241\261\032\341'

  def Parse(self, filehandle):
    """Extract EventObjects from a file."""

    if self.MAGIC not in filehandle.read(len(self.MAGIC)):
      raise errors.UnableToParseFile(
          u'[%s] unable to parse file %s: %s' % (
              self.parser_name, filehandle.name, 'Not an OLE File.'))

    try:
      loader = OleFileIO_PL.OleFileIO(filehandle)
    except RuntimeError as exception:
      raise errors.UnableToParseFile(
          u'[%s] unable to parse file %s: %s' % (
              self.parser_name, filehandle.name, exception))

    try:
      metadata = loader.get_metadata()
    except (OverflowError, IndexError, ValueError) as exception:
      raise errors.UnableToParseFile(
          u'[%s] unable to parse file %s: %s' % (
              self.parser_name, filehandle.name, exception))

    container = event.EventContainer()
    container.offset = 0
    container.data_type = self.DATA_TYPE

    container.codepage = self.SetValue(metadata.codepage)
    container.title = self.SetValue(metadata.title)
    container.subject = self.SetValue(metadata.subject)
    container.author = self.SetValue(metadata.author)
    container.keywords = self.SetValue(metadata.keywords)
    container.comments = self.SetValue(metadata.comments)
    container.template = self.SetValue(metadata.template)
    container.last_saved_by = self.SetValue(
        metadata.last_saved_by)
    container.revision_num = self.SetValue(
        metadata.revision_number)
    container.total_edit_time = self.SetValue(
        metadata.total_edit_time)
    container.num_pages = self.SetValue(metadata.num_pages)
    container.num_words = self.SetValue(metadata.num_words)
    container.num_chars = self.SetValue(metadata.num_chars)
    container.creating_application = self.SetValue(
        metadata.creating_application)
    container.security = self.SetValue(metadata.security)
    container.company = self.SetValue(metadata.company)
    container.manager = self.SetValue(metadata.manager)
    container.slides = self.SetValue(metadata.slides)
    container.hidden_slides = self.SetValue(metadata.hidden_slides)
    container.version = self.SetValue(metadata.version)
    container.doc_version = self.SetValue(metadata.doc_version)
    container.notes = self.SetValue(metadata.notes)
    container.dig_sig = self.SetValue(metadata.dig_sig)
    container.shared = self.SetValue(metadata.shared_doc)
    container.language = self.SetValue(metadata.language)
    container.mm_clips = self.SetValue(metadata.mm_clips)

    created_date = metadata.create_time
    if isinstance(created_date, datetime.datetime):
      container.Append(OLE2Event(
          created_date,eventdata.EventTimestamp.CREATION_TIME))

    modified_date = metadata.last_saved_time
    if isinstance(modified_date, datetime.datetime):
      container.Append(OLE2Event(
          modified_date,eventdata.EventTimestamp.MODIFICATION_TIME))

    lastprinted_date = metadata.last_printed
    if isinstance(lastprinted_date, datetime.datetime):
      container.Append(OLE2Event(
          lastprinted_date, eventdata.EventTimestamp.LAST_PRINTED))

    return container

  def SetValue(self, value):
    """Strip null chars from str or unicode values."""
    if type(value) in (str, unicode):
      value = value.strip('\x00')
    return value


class OLE2Event(event.TimestampEvent):
  """Process timestamps from OLECF Events."""

  DATA_TYPE = 'metadata:OLECF'

  def __init__(self, dt_timestamp, usage):
    """An EventObject created from an OLE2 entry.

    Args:
      dt_timestamp: A python datetime.datetime object.
      usage: The description of the usage of the time value.
    """
    timestamp = timelib.Timestamp.FromPythonDatetime(dt_timestamp)
    super(OLE2Event, self).__init__(timestamp, usage, self.DATA_TYPE)
