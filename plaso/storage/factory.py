# -*- coding: utf-8 -*-
"""This file contains the storage factory class."""

from __future__ import unicode_literals

from plaso.storage import sqlite_file as storage_sqlite_file


class StorageFactory(object):
  """Storage factory."""

  @classmethod
  def CreateStorageFileForFile(cls, path):
    """Creates a storage file based on the file.

    Args:
      path (str): path to the storage file.

    Returns:
      StorageFile: a storage file or None if the storage file cannot be
          opened or the storage format is not supported.
    """
    if storage_sqlite_file.SQLiteStorageFile.CheckSupportedFormat(path):
      return storage_sqlite_file.SQLiteStorageFile()

  @classmethod
  def CreateStorageReaderForFile(cls, path):
    """Creates a storage reader based on the file.

    Args:
      path (str): path to the storage file.

    Returns:
      StorageReader: a storage reader or None if the storage file cannot be
          opened or the storage format is not supported.
    """
    if storage_sqlite_file.SQLiteStorageFile.CheckSupportedFormat(path):
      return storage_sqlite_file.SQLiteStorageFileReader(path)

  @classmethod
  def CreateStorageWriterForFile(cls, session, path):
    """Creates a storage writer based on the file.

    Args:
      session (Session): session the storage changes are part of.
      path (str): path to the storage file.

    Returns:
      StorageWriter: a storage writer or None if the storage file cannot be
          opened or the storage format is not supported.
    """
    if storage_sqlite_file.SQLiteStorageFile.CheckSupportedFormat(path):
      return storage_sqlite_file.SQLiteStorageFileWriter(session, path)
