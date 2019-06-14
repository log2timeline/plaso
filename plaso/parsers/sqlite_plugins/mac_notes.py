# -*- coding: utf-8 -*-
"""Parser for mac notes database.

SQLite database path: test_data/NotesV7.storedata
SQLite database Name: NotesV7.storedata
"""

from __future__ import unicode_literals

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import py2to3
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface

# pylint: disable=import-error
if py2to3.PY_2:
  import HTMLParser
else:
  import html.parser as HTMLParser


class _ZHTMLStringTextExtractor(HTMLParser.HTMLParser):
  """HTML parser for extracting text from a mac notes zhtmlstring."""

  # This method is part of the HTMLParser interface.
  # pylint: disable=invalid-name
  def handle_data(self, data):
    """Called to handle arbitrary data processed by the parser.

    Args:
      data(str): arbitrry data processed by the parser, such as text nodes and
          the content of <script>...</script> and <style>...</style>.
    """
    # Not defined in init due to Python2/Python3 complications.
    # pylint: disable=attribute-defined-outside-init
    self._text.append(data)

  def ExtractText(self, zhtmlstring):
    """Extracts text from a Mac notes ZHTMLString.

    Args:
      zhtmlstring (str): zhtmlstring from a Mac notes database.

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


class MacNotesEventData(events.EventData):
  """Mac Notes event data.

  Attributes:
    text (str): note text.
    title (str): note title.
  """

  DATA_TYPE = 'mac:notes:note'

  def __init__(self):
    """Initializes event data."""
    super(MacNotesEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.text = None
    self.title = None


class MacNotesPlugin(interface.SQLitePlugin):
  """Plugin for the Mac OS Notes database."""

  NAME = 'mac_notes'
  DESCRIPTION = 'Parser for Mac Notes'

  QUERIES = [('SELECT nb.ZHTMLSTRING AS zhtmlstring, '
              'n.ZDATECREATED AS timestamp, '
              'n.ZDATEEDITED AS last_modified_time, n.ZTITLE as title '
              'FROM ZNOTEBODY nb, ZNOTE n '
              'WHERE nb.Z_PK = n.Z_PK', 'ParseZHTMLSTRINGRow')]

  REQUIRED_TABLES = frozenset(['ZNOTEBODY', 'ZNOTE'])

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
          'VARCHAR, Z_SUPER INTEGER, Z_MAX INTEGER)')
  }]

  def ParseZHTMLSTRINGRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a row from the database.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      query (str): query that created the row.
      row (sqlite3.Row): row resulting from query.
    """
    # Note that pysqlite does not accept a Unicode string in row['string'] and
    # will raise "IndexError: Index must be int or string".
    query_hash = hash(query)
    event_data = MacNotesEventData()

    zhtmlstring = self._GetRowValue(query_hash, row, 'zhtmlstring')

    text_extractor = _ZHTMLStringTextExtractor()
    text = text_extractor.ExtractText(zhtmlstring)
    event_data.text = text

    event_data.title = self._GetRowValue(query_hash, row, 'title')
    timestamp = self._GetRowValue(query_hash, row, 'timestamp')

    date_time = dfdatetime_cocoa_time.CocoaTime(timestamp=timestamp)
    event = time_events.DateTimeValuesEvent(
        date_time, definitions.TIME_DESCRIPTION_CREATION)
    parser_mediator.ProduceEventWithEventData(event, event_data)

    timestamp = self._GetRowValue(query_hash, row, 'last_modified_time')
    if timestamp:
      date_time = dfdatetime_cocoa_time.CocoaTime(
          timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_LAST_USED)
      parser_mediator.ProduceEventWithEventData(event, event_data)


sqlite.SQLiteParser.RegisterPlugin(MacNotesPlugin)
