# -*- coding: utf-8 -*-
"""This file contains the storage factory class."""

from plaso.lib import definitions

from plaso.storage.sqlite import reader as sqlite_reader
from plaso.storage.sqlite import sqlite_file
from plaso.storage.sqlite import writer as sqlite_writer

try:
  from plaso.storage.redis import reader as redis_reader
  from plaso.storage.redis import writer as redis_writer
except ModuleNotFoundError:
  redis_reader = None
  redis_writer = None


class StorageFactory(object):
  """Storage factory."""

  @classmethod
  def CreateStorageFile(cls, storage_format):
    """Creates a storage file.

    Args:
      storage_format (str): storage format.

    Returns:
      StorageFile: a storage file or None if the storage file cannot be
          opened or the storage format is not supported.
    """
    if storage_format == definitions.STORAGE_FORMAT_SQLITE:
      return sqlite_file.SQLiteStorageFile()

    return None

  @classmethod
  def CreateStorageReaderForFile(cls, path):
    """Creates a storage reader based on the file.

    Args:
      path (str): path to the storage file.

    Returns:
      StorageReader: a storage reader or None if the storage file cannot be
          opened or the storage format is not supported.
    """
    if sqlite_file.SQLiteStorageFile.CheckSupportedFormat(path):
      return sqlite_reader.SQLiteStorageFileReader(path)

    return None

  @classmethod
  def CreateStorageWriter(cls, storage_format):
    """Creates a storage writer.

    Args:
      storage_format (str): storage format.

    Returns:
      StorageWriter: a storage writer or None if the storage file cannot be
          opened or the storage format is not supported.
    """
    if storage_format == definitions.STORAGE_FORMAT_SQLITE:
      return sqlite_writer.SQLiteStorageFileWriter()

    if storage_format == definitions.STORAGE_FORMAT_REDIS and redis_writer:
      return redis_writer.RedisStorageWriter()

    return None

  @classmethod
  def CreateStorageWriterForFile(cls, path):
    """Creates a storage writer based on the file.

    Args:
      path (str): path to the storage file.

    Returns:
      StorageWriter: a storage writer or None if the storage file cannot be
          opened or the storage format is not supported.
    """
    if sqlite_file.SQLiteStorageFile.CheckSupportedFormat(path):
      return sqlite_writer.SQLiteStorageFileWriter()

    return None

  @classmethod
  def CreateTaskStorageReader(cls, storage_format, task, path):
    """Creates a task storage reader.

    Args:
      storage_format (str): storage format.
      task (Task): task the storage changes are part of.
      path (str): path to the storage file.

    Returns:
      StorageReader: a storage reader or None if the storage file cannot be
          opened or the storage format is not supported.
    """
    if storage_format == definitions.STORAGE_FORMAT_SQLITE:
      return sqlite_reader.SQLiteStorageFileReader(path)

    if storage_format == definitions.STORAGE_FORMAT_REDIS and redis_reader:
      return redis_reader.RedisStorageReader(
          task.session_identifier, task.identifier)

    return None

  @classmethod
  def CreateTaskStorageWriter(cls, storage_format):
    """Creates a task storage writer.

    Args:
      storage_format (str): storage format.

    Returns:
      StorageWriter: a storage writer or None if the storage file cannot be
          opened or the storage format is not supported.
    """
    if storage_format == definitions.STORAGE_FORMAT_SQLITE:
      return sqlite_writer.SQLiteStorageFileWriter(
          storage_type=definitions.STORAGE_TYPE_TASK)

    if storage_format == definitions.STORAGE_FORMAT_REDIS and redis_writer:
      return redis_writer.RedisStorageWriter(
          storage_type=definitions.STORAGE_TYPE_TASK)

    return None
