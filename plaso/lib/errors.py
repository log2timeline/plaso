#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2012 The Plaso Project Authors.
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
"""This file contains the error classes."""

class Error(Exception):
  """Base error class."""


class CollectorError(Exception):
  """Class that defines collector errors."""


class TimestampNotCorrectlyFormed(Error):
  """Raised when there is an error adding a timestamp to an EventObject."""


class NotAnEventContainerOrObject(Error):
  """Expect an EventContainer/EventObject yet don't get it it's faulty."""


class UnableToParseFile(Error):
  """Raised when a parser is not designed to parse a file."""


class WrongProtobufEntry(Error):
  """Raised when an EventObject cannot be serialized as a protobuf."""


class UnableToOpenFile(Error):
  """Raised when a PlasoFile class attempts to open a file it cannot open."""


class SameFileType(Error):
  """Raised when a PFile is being evaluated against the same driver type."""


class BadConfigOption(Error):
  """Raised when the engine is started with a faulty parameter."""


class PreProcessFail(Error):
  """Raised when a preprocess module is unable to gather information."""


class PathNotFound(Error):
  """Raised when a preprocessor fails to fill in a path variable."""


class QueueEmpty(Error):
  """Class that implements a queue empty exception."""


class UnableToOpenFilesystem(Error):
  """Raised when unable to open filesystem."""


class WrongFormatter(Error):
  """Raised when the formatter is not applicable for a particular event."""


class NoFormatterFound(Error):
  """Raised when no formatter is found for a particular event."""


class WinRegistryValueError(Error):
  """Raised when there is an issue reading a registry value."""


class WrongPlugin(Error):
  """Raised when the plugin is of the wrong type."""


class WrongPlistPlugin(Error):
  """Error reporting wrong plist plugin used."""


class WrongBencodePlugin(Error):
  """Error reporting wrong bencode plugin used."""


class NotAText(Error):
  """Raised when trying to read a text on a non-text sample."""
