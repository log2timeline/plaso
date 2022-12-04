# -*- coding: utf-8 -*-
"""SQLite parser plugin for MacOS Notes database files."""

import html.parser as HTMLParser

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class _ZHTMLStringTextExtractor(HTMLParser.HTMLParser):
  """HTML parser for extracting text from a MacOS notes zhtmlstring."""

  # pylint: disable=abstract-method
  # Method 'error' is abstract in class 'ParserBase' but is not overridden

  # This method is part of the HTMLParser interface.
  # pylint: disable=invalid-name
  def handle_data(self, data):
    """Called to handle arbitrary data processed by the parser.

    Args:
      data(str): arbitrary data processed by the parser, such as text nodes and
          the content of <script>...</script> and <style>...</style>.
    """
    # Not defined in init due to Python2/Python3 complications.
    # pylint: disable=attribute-defined-outside-init
    self._text.append(data)

  def ExtractText(self, zhtmlstring):
    """Extracts text from a MacOS notes ZHTMLString.

    Args:
      zhtmlstring (str): zhtmlstring from a MacOS notes database.

    Returns:
      str: the text of the note, with HTML removed.
    """
    # Not defined in init due to Python2/Python3 complications.
    # pylint: disable=attribute-defined-outside-init
    self._text = []
    self.feed(zhtmlstring)
    self.close()
    self._text = [line.strip() for line in self._text]
    return ' '.join(self._text)


class MacOSNotesEventData(events.EventData):
  """MacOS Notes event data.

  Attributes:
    creation_time (dfdatetime.DateTimeValues): date and time the notes database
        entry was created.
    modification_time (dfdatetime.DateTimeValues): date and time the notes
        database entry was last modified.
    text (str): note text.
    title (str): note title.
  """

  DATA_TYPE = 'macos:notes:entry'

  def __init__(self):
    """Initializes event data."""
    super(MacOSNotesEventData, self).__init__(data_type=self.DATA_TYPE)
    self.creation_time = None
    self.modification_time = None
    self.text = None
    self.title = None


class MacOSNotesPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for MacOS notes database files.

  The MacOS Notes database file is typically stored in:
  test_data/NotesV7.storedata
  """

  NAME = 'mac_notes'
  DATA_FORMAT = 'MacOS Notes SQLite database (NotesV7.storedata) file'

  QUERIES = [(
      ('SELECT ZNOTEBODY.ZHTMLSTRING AS zhtmlstring, '
       'ZNOTE.ZDATECREATED AS timestamp, '
       'ZNOTE.ZDATEEDITED AS last_modified_time, '
       'ZNOTE.ZTITLE as title '
       'FROM ZNOTEBODY, ZNOTE WHERE ZNOTEBODY.Z_PK = ZNOTE.Z_PK'),
      'ParseZHTMLSTRINGRow')]

  REQUIRED_STRUCTURE = {
      'ZNOTEBODY': frozenset([
          'ZHTMLSTRING']),
      'ZNOTE': frozenset([
          'ZDATECREATED', 'ZDATEEDITED', 'ZTITLE'])}

  SCHEMAS = [{
      'ZACCOUNT': (
          'CREATE TABLE ZACCOUNT ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER,'
          'Z_OPT INTEGER, ZALLOWINSECUREAUTHENTICATION INTEGER,'
          'ZDIDCHOOSETOMIGRATE INTEGER, ZENABLED INTEGER, ZROOTFOLDER'
          'INTEGER, Z6_ROOTFOLDER INTEGER, ZTRASHFOLDER INTEGER,'
          'ZGMAILCAPABILITIESSUPPORT INTEGER, ZPORT INTEGER,'
          'ZSECURITYLAYERTYPE INTEGER, ZMIGRATIONOFFERED INTEGER,'
          'ZACCOUNTDESCRIPTION VARCHAR, ZEMAILADDRESS VARCHAR, ZFULLNAME'
          'VARCHAR, ZPARENTACACCOUNTIDENTIFIER VARCHAR, ZUSERNAME VARCHAR,'
          'ZFOLDERHIERARCHYSYNCSTATE VARCHAR, ZAUTHENTICATION VARCHAR,'
          'ZHOSTNAME VARCHAR, ZSERVERPATHPREFIX VARCHAR, ZEXTERNALURL BLOB,'
          'ZINTERNALURL BLOB, ZLASTUSEDAUTODISCOVERURL BLOB,'
          'ZTLSCERTIFICATE BLOB )'),
      'ZATTACHMENT': (
          'CREATE TABLE ZATTACHMENT ( Z_PK INTEGER PRIMARY KEY, Z_ENT'
          'INTEGER, Z_OPT INTEGER, ZNOTE INTEGER, Z10_NOTE INTEGER,'
          'ZCONTENTID VARCHAR, ZFILEURL BLOB )'),
      'ZFOLDER': (
          'CREATE TABLE ZFOLDER ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER,'
          'Z_OPT INTEGER, ZACCOUNT INTEGER, Z1_ACCOUNT INTEGER, ZPARENT'
          'INTEGER, Z6_PARENT INTEGER, ZISDISTINGUISHED INTEGER,'
          'ZALLEGEDHIGHESTMODIFICATIONSEQUENCE INTEGER,'
          'ZCOMPUTEDHIGHESTMODIFICATIONSEQUENCE INTEGER, ZUIDNEXT INTEGER,'
          'ZUIDVALIDITY INTEGER, ZTRASHACCOUNT INTEGER, Z1_TRASHACCOUNT'
          'INTEGER, ZNAME VARCHAR, ZCHANGEKEY VARCHAR, ZFOLDERID VARCHAR,'
          'ZSYNCSTATE VARCHAR, ZSERVERNAME VARCHAR )'),
      'ZNOTE': (
          'CREATE TABLE ZNOTE ( Z_PK INTEGER PRIMARY KEY, Z_ENT INTEGER,'
          'Z_OPT INTEGER, ZBODY INTEGER, ZFOLDER INTEGER, Z6_FOLDER'
          'INTEGER, ZMIMEDATASIZE INTEGER, ZDATECREATED TIMESTAMP,'
          'ZDATEEDITED TIMESTAMP, ZREMOTEID VARCHAR, ZTITLE VARCHAR,'
          'ZCHANGEKEY VARCHAR, ZUNIVERSALLYUNIQUEID BLOB )'),
      'ZNOTEBODY': (
          'CREATE TABLE ZNOTEBODY ( Z_PK INTEGER PRIMARY KEY, Z_ENT'
          'INTEGER, Z_OPT INTEGER, ZNOTE INTEGER, Z10_NOTE INTEGER,'
          'ZHTMLSTRING VARCHAR )'),
      'ZOFFLINEACTION': (
          'CREATE TABLE ZOFFLINEACTION ( Z_PK INTEGER PRIMARY KEY, Z_ENT'
          'INTEGER, Z_OPT INTEGER, ZSEQUENCENUMBER INTEGER, ZACCOUNT'
          'INTEGER, Z1_ACCOUNT INTEGER, ZFOLDER INTEGER, Z6_FOLDER INTEGER,'
          'ZPARENT INTEGER, Z6_PARENT INTEGER, ZORIGINALPARENT INTEGER,'
          'Z6_ORIGINALPARENT INTEGER, ZFOLDER1 INTEGER, Z6_FOLDER1 INTEGER,'
          'ZNOTE INTEGER, Z10_NOTE INTEGER, ZORIGINALFOLDER INTEGER,'
          'Z6_ORIGINALFOLDER INTEGER )'),
      'Z_METADATA': (
          'CREATE TABLE Z_METADATA (Z_VERSION INTEGER PRIMARY KEY, Z_UUID'
          'VARCHAR(255), Z_PLIST BLOB)'),
      'Z_MODELCACHE': ('CREATE TABLE Z_MODELCACHE (Z_CONTENT BLOB)'),
      'Z_PRIMARYKEY': (
          'CREATE TABLE Z_PRIMARYKEY (Z_ENT INTEGER PRIMARY KEY, Z_NAME'
          'VARCHAR, Z_SUPER INTEGER, Z_MAX INTEGER)')}]

  def _GetDateTimeRowValue(self, query_hash, row, value_name):
    """Retrieves a date and time value from the row.

    Args:
      query_hash (int): hash of the query, that uniquely identifies the query
          that produced the row.
      row (sqlite3.Row): row.
      value_name (str): name of the value.

    Returns:
      dfdatetime.CocoaTime: date and time value or None if not available.
    """
    timestamp = self._GetRowValue(query_hash, row, value_name)
    if timestamp is None:
      return None

    return dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)

  def ParseZHTMLSTRINGRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a row from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row resulting from query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".
    query_hash = hash(query)

    zhtmlstring = self._GetRowValue(query_hash, row, 'zhtmlstring')

    text_extractor = _ZHTMLStringTextExtractor()
    text = text_extractor.ExtractText(zhtmlstring)

    event_data = MacOSNotesEventData()
    event_data.creation_time = self._GetDateTimeRowValue(
        query_hash, row, 'timestamp')
    event_data.modification_time = self._GetDateTimeRowValue(
        query_hash, row, 'last_modified_time')
    event_data.text = text
    event_data.title = self._GetRowValue(query_hash, row, 'title')

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(MacOSNotesPlugin)
