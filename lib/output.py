#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""This file contains the interface for output parsing of plaso.

The default output or storage mechanism of Plaso is not in a human
readable format. There needs to be a way to define the output in such
a way.

After the timeline is collected and stored another tool can read, filter,
sort and process the output inside the storage, and send each processed
entry to an output formatter that takes care of parsing the output into
a human readable format for easy human consumption/analysis.

"""

import sys
import StringIO
import pytz

from plaso.lib import registry


class LogOutputFormatter(object):
  """A base class for formatting output produced by plaso.

  This class exists mostly for documentation purposes. Subclasses should
  override the relevant methods to act on the callbacks.
  """

  __metaclass__ = registry.MetaclassRegistry
  __abstract = True

  def __init__(self, filehandle=sys.stdout, zone=pytz.utc):
    """Constructor for the output module.

    Args:
      filehandle: A file-like object that can be written to.
      zone: The output time zone (a pytz object).
    """
    self.zone = zone
    self.filehandle = filehandle

  def WriteEvent(self, evt):
    """Write the output of a single entry to the output filehandle.

    This method takes care of actually outputting each event in
    question. It does so by first prepending it with potential
    start of event, then processes the main body before appending
    a potential end of event.

    Args:
      evt: An EventObject, defined in the event library.
    """
    self.StartEvent()
    self.EventBody(evt)
    self.EndEvent()

  def EventBody(self, evt):
    """Writes the main body of an event to the output filehandle.

    Args:
      evt: An EventObject, defined in the event library.

    Raises:
      NotImplementedError: When not implemented.
    """
    raise NotImplementedError

  def StartEvent(self):
    """This should be extended by specific implementations.

    This method does all pre-processing or output before each event
    is printed, for instance to surround XML events with tags, etc.
    """
    self.filehandle.write('')

  def EndEvent(self):
    """This should be extended by specific implementations.

    This method does all the post-processing or output after
    each event has been printed, such as closing XML tags, etc.
    """
    self.filehandle.write('')

  def Start(self):
    """This should be extended by specific implementations.

    Depending on the file format of the output it may need
    a header. This method should return a header if one is
    defined in that output format.
    """
    self.filehandle.write('')

  def End(self):
    """This should be extended by specific implementations.

    Depending on the file format of the output it may need
    a footer. This method should return a footer if one is
    defined in that output format.
    """
    self.filehandle.write('')

  def Usage(self):
    """Return a quick help message that describes the output provided."""
    return 'This is a generic output module that provides no context.'


class FileLogOutputFormatter(LogOutputFormatter):
  """A simple file based output formatter."""

  __abstract = True

  def __init__(self, filehandle=sys.stdout, zone=pytz.utc):
    """Set up the formatter."""
    super(FileLogOutputFormatter, self).__init__(filehandle, zone)
    if not isinstance(filehandle, (file, StringIO.StringIO)):
      self.filehandle = open(filehandle, 'w')

  def End(self):
    """Close the open filehandle after the last output."""
    super(FileLogOutputFormatter, self).End()
    self.filehandle.close()


def ListOutputFormatters():
  """Generate a list of all available output formatters."""
  for cl in LogOutputFormatter.classes:
    yield cl, LogOutputFormatter.classes[cl]().Usage()
