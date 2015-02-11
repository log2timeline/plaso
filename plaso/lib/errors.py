# -*- coding: utf-8 -*-
"""This file contains the error classes."""

class Error(Exception):
  """Base error class."""


class BadConfigOption(Error):
  """Raised when the engine is started with a faulty parameter."""


class CollectorError(Error):
  """Class that defines collector errors."""


class NotAText(Error):
  """Raised when trying to read a text on a non-text sample."""


class NoFormatterFound(Error):
  """Raised when no formatter is found for a particular event."""


class PathNotFound(Error):
  """Raised when a preprocessor fails to fill in a path variable."""


class PreProcessFail(Error):
  """Raised when a preprocess module is unable to gather information."""


class ProxyFailedToStart(Error):
  """Raised when unable to start a proxy."""


class QueueEmpty(Error):
  """Class that implements a queue empty exception."""


class QueueFull(Error):
  """Class that implements a queue full exception."""


class SameFileType(Error):
  """Raised when a file is being evaluated against the same driver type."""


class SourceScannerError(Error):
  """Class that defines source scanner errors."""


class TimestampNotCorrectlyFormed(Error):
  """Raised when there is an error adding a timestamp to an EventObject."""


class UnableToOpenFile(Error):
  """Raised when a PlasoFile class attempts to open a file it cannot open."""


class UnableToOpenFilesystem(Error):
  """Raised when unable to open filesystem."""


class UnableToParseFile(Error):
  """Raised when a parser is not designed to parse a file."""


class UserAbort(Error):
  """Class that defines an user initiated abort exception."""


class WrongBencodePlugin(Error):
  """Error reporting wrong bencode plugin used."""


class WrongFilterOption(Error):
  """Raised when the filter option is badly formed."""


class WrongFormatter(Error):
  """Raised when the formatter is not applicable for a particular event."""


class WrongPlistPlugin(Error):
  """Error reporting wrong plist plugin used."""


class WrongPlugin(Error):
  """Raised when the plugin is of the wrong type."""


class WrongProtobufEntry(Error):
  """Raised when an EventObject cannot be serialized as a protobuf."""


class WinRegistryValueError(Error):
  """Raised when there is an issue reading a registry value."""
