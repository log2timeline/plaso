# -*- coding: utf-8 -*-
"""Parser for the Mac OS X Document Versions files."""

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


__author__ = 'Joaquin Moreno Garijo (Joaquin.MorenoGarijo.2013@live.rhul.ac.uk)'


class MacDocumentVersionsEvent(time_events.PosixTimeEvent):
  """Convenience class for a entry from the Document Versions database."""

  DATA_TYPE = 'mac:document_versions:file'

  def __init__(self, posix_time, name, path, version_path, last_time, user_sid):
    """Initializes the event object.

    Args:
      posix_time: The POSIX time value.
      name: name of the original file.
      path: path from the original file.
      version_path: path to the version copy of the original file.
      last_time: the system user ID of the user that opened the file.
      user_sid: identification user ID that open the file.
    """
    super(MacDocumentVersionsEvent, self).__init__(
        posix_time, eventdata.EventTimestamp.CREATION_TIME)

    self.name = name
    self.path = path
    self.version_path = version_path
    # TODO: shouldn't this be a separate event?
    self.last_time = last_time
    self.user_sid = unicode(user_sid)


class MacDocumentVersionsPlugin(interface.SQLitePlugin):
  """Parse the Mac OS X Document Versions SQLite database.."""

  NAME = 'mac_document_versions'
  DESCRIPTION = u'Parser for document revisions SQLite database files.'

  # Define the needed queries.
  # name: name from the original file.
  # path: path from the original file (include the file)
  # last_time: last time when the file was replicated.
  # version_path: path where the version is stored.
  # version_time: the timestamp when the version was created.
  QUERIES = [
      (('SELECT f.file_name AS name, f.file_path AS path, '
        'f.file_last_seen AS last_time, g.generation_path AS version_path, '
        'g.generation_add_time AS version_time FROM files f, generations g '
        'WHERE f.file_storage_id = g.generation_storage_id;'),
       'DocumentVersionsRow')]

  # The required tables for the query.
  REQUIRED_TABLES = frozenset(['files', 'generations'])

  # The SQL field path is the relative path from DocumentRevisions.
  # For this reason the Path to the program has to be added at the beginning.
  ROOT_VERSION_PATH = u'/.DocumentRevisions-V100/'

  def DocumentVersionsRow(
      self, parser_mediator, row, query=None, **unused_kwargs):
    """Parses a document versions row.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      row: The row resulting from the query.
      query: Optional query string. The default is None.
    """
    # version_path = "PerUser/UserID/xx/client_id/version_file"
    # where PerUser and UserID are a real directories.
    paths = row['version_path'].split(u'/')
    if len(paths) < 2 or not paths[1].isdigit():
      user_sid = None
    else:
      user_sid = paths[1]
    version_path = self.ROOT_VERSION_PATH + row['version_path']
    path, _, _ = row['path'].rpartition(u'/')

    event_object = MacDocumentVersionsEvent(
        row['version_time'], row['name'], path, version_path,
        row['last_time'], user_sid)
    parser_mediator.ProduceEvent(event_object, query=query)


sqlite.SQLiteParser.RegisterPlugin(MacDocumentVersionsPlugin)
