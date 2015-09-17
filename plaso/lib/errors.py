# -*- coding: utf-8 -*-
"""This file contains the error classes."""

class Error(Exception):
  """Base error class."""


class BadConfigObject(Error):
  """Raised when the CLI argument helper is of the wrong type."""


class BadConfigOption(Error):
  """Raised when the engine is started with a faulty parameter."""


class CollectorError(Error):
  """Class that defines collector errors."""


class ConnectionError(Error):
  """Class that defines errors encountered connecting to a service."""


class EngineAbort(Error):
  """Class that defines an engine initiated abort exception."""


class FileSystemScannerError(Error):
  """Raised when a there is an issue scanning for a file system."""


class NotAText(Error):
  """Raised when trying to read a text on a non-text sample."""


class NoFormatterFound(Error):
  """Raised when no formatter is found for a particular event."""


class ParseError(Error):
  """Raised when a parse error occurred."""


class PathNotFound(Error):
  """Raised when a preprocessor fails to fill in a path variable."""


class PreProcessFail(Error):
  """Raised when a preprocess module is unable to gather information."""


class ProxyFailedToStart(Error):
  """Raised when unable to start a proxy."""


class QueueAlreadyClosed(Error):
  """Raised when an attempt is made to close a queue that's already closed."""


class QueueAlreadyStarted(Error):
  """Raised when an attempt is made to start queue that's already started."""


class QueueClose(Error):
  """Class that implements a queue close exception."""


class QueueEmpty(Error):
  """Class that implements a queue empty exception."""


class QueueFull(Error):
  """Class that implements a queue full exception."""


class SameFileType(Error):
  """Raised when a file is being evaluated against the same driver type."""


class SourceScannerError(Error):
  """Class that defines source scanner errors."""


class TimestampError(Error):
  """Class that defines timestamp errors."""


class UnableToLoadRegistryHelper(Error):
  """Raised when unable to load a Registry helper object."""


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


class WrongFormatter(Error):
  """Raised when the formatter is not applicable for a particular event."""


class WrongPlistPlugin(Error):
  """Error reporting wrong plist plugin used."""


class WrongQueueType(Error):
  """Raised when an unsupported operation is attempted on a queue.

  For example, attempting to Pop from a Push-only queue.
  """


class WrongPlugin(Error):
  """Raised when the plugin is of the wrong type."""


class WrongProtobufEntry(Error):
  """Raised when an EventObject cannot be serialized as a protobuf."""
