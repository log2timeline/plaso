# -*- coding: utf-8 -*-
"""SQLite plugin for parsing Apple Notes (NoteStore.sqlite)."""

from dfdatetime import cocoa_time as dfdatetime_cocoa_time

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class IOSNotesEventData(events.EventData):
    """SQLite plugin for Apple Notes."""

    NAME = 'apple_notes'
    DESCRIPTION = 'Parser for Apple Notes SQLite database files.'

    REQUIRED_TABLES = frozenset(['ATRANSACTION', 'ZICCLOUDSYNCINGOBJECT', 'ZICNOTEDATA'])

    QUERIES = [
        ('SELECT ATRANSACTION.ZTIMESTAMP AS timestamp, '
         'ZICCLOUDSYNCINGOBJECT.Z_PK AS note_id, '
         'ZICCLOUDSYNCINGOBJECT.ZTITLE AS title, '
         'ZICCLOUDSYNCINGOBJECT.ZTITLE1 AS title1, '
         'ZICCLOUDSYNCINGOBJECT.ZSUMMARY AS summary, '
         'ZICCLOUDSYNCINGOBJECT.ZCREATIONDATE AS creation_date, '
         'ZICCLOUDSYNCINGOBJECT.ZMODIFICATIONDATE AS modification_date, '
         'ZICNOTEDATA.ZDATA AS content '
         'FROM ATRANSACTION '
         'LEFT JOIN ZICCLOUDSYNCINGOBJECT ON ATRANSACTION.Z_PK = ZICCLOUDSYNCINGOBJECT.Z_PK '
         'LEFT JOIN ZICNOTEDATA ON ZICCLOUDSYNCINGOBJECT.ZNOTEDATA = ZICNOTEDATA.Z_PK',
         'ParseAppleNotes')]

    def ParseAppleNotes(self, parser_mediator, query, row, **unused_kwargs):
        """Parses a row from the database."""
        note_id = row['note_id']
        timestamp = self._GetDateTimeFromRow(row, 'timestamp')
        title = row.get('title')
        title1 = row.get('title1')
        summary = row.get('summary')
        content = self._DecodeContent(row.get('content'))
        creation_date = self._GetDateTimeFromRow(row, 'creation_date')
        modification_date = self._GetDateTimeFromRow(row, 'modification_date')

        # Combine fields into a human-readable message
        readable_message = self._GenerateReadableMessage(title, title1, summary, content)

        event_data = AppleNotesEventData()
        event_data.note_id = note_id
        event_data.timestamp = timestamp
        event_data.title = title
        event_data.title1 = title1
        event_data.summary = summary
        event_data.content = content
        event_data.creation_date = creation_date
        event_data.modification_date = modification_date
        event_data.message = readable_message

        parser_mediator.ProduceEventData(event_data)

    def _DecodeContent(self, content_blob):
        """Decodes the content of a note, if it is stored as a BLOB."""
        if not content_blob:
            return None
        try:
            # Decode assuming UTF-8 or similar encoding
            return content_blob.decode('utf-8')
        except (AttributeError, UnicodeDecodeError):
            # Handle cases where content is not plain text
            return str(content_blob)

    def _GenerateReadableMessage(self, title, title1, summary, content):
        """Generates a human-readable message from note fields."""
        parts = []
        if title:
            parts.append(f"Title: {title}")
        if title1:
            parts.append(f"Alternate Title: {title1}")
        if summary:
            parts.append(f"Summary: {summary}")
        if content:
            parts.append(f"Content: {content}")
        return " | ".join(parts) if parts else "No content available"


class AppleNotesEventData(events.EventData):
    """Apple Notes event data."""

    DATA_TYPE = 'apple:notes:note'

    def __init__(self):
        """Initializes event data."""
        super(AppleNotesEventData, self).__init__(data_type=self.DATA_TYPE)
        self.note_id = None
        self.timestamp = None
        self.title = None
        self.title1 = None
        self.summary = None
        self.content = None
        self.creation_date = None
        self.modification_date = None
        self.message = None


sqlite.SQLiteParser.RegisterPlugin(AppleNotesPlugin)
