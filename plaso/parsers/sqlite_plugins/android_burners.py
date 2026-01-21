# -*- coding: utf-8 -*-
"""SQLite parser plugin for Android communication
  information (burners) database files."""

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface

class AndroidCommunicationInformationEventData(events.EventData):
  """Android Communication Information event data.

  Attributes:
    phone_number_id (str): Identifier for the associated phone number.
    voicemail_url (str): URL for accessing the voicemail
      associated with the burner.
    user_id (str): ID of the user associated with the burner.
    name (str): Name of the burner.
    alias (str): Alias or nickname for the burner.
    features (str): Features enabled for the burner.
    total_minutes (int): Total minutes available for calls on the burner.
    expiration_date (datetime): Expiration date of the burner.
    date_created (datetime): Date the burner was created.
    last_updated_date (datetime): Last update date
      of the burner record.
    renewal_date (datetime): Renewal date for the burner.
  """

  DATA_TYPE = 'android:burners'

  def __init__(self):
    """Initializes event data."""
    super(AndroidCommunicationInformationEventData,
          self).__init__(data_type=self.DATA_TYPE)
    self.phone_number_id = None
    self.voicemail_url = None
    self.user_id = None
    self.name = None
    self.alias = None
    self.features = None
    self.total_minutes = None
    self.expiration_date = None
    self.date_created = None
    self.last_updated_date = None
    self.renewal_date = None

class AndroidCommunicationInformationPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Android communication information database files.
    
    The Android communication information database file is typically stored in:
    burners.db
  """

  NAME = 'android_communication_information'
  DATA_FORMAT = 'Android communication information SQLite database file'

  REQUIRED_STRUCTURE = {
    'burners': frozenset(['_id', 'phone_number_id', 'voicemail_url',
                            'user_id', 'name', 'alias', 'features',
                            'total_minutes', 'expiration_date',
                            'date_created', 'last_updated_date',
                            'renewal_date'])
  }

  QUERIES = [(
    """SELECT _id AS id, phone_number_id, voicemail_url, user_id, name, alias,
    features, total_minutes, expiration_date, date_created, last_updated_date,
    renewal_date FROM burners""", 'ParseCommunicationInformationRow'
  )]

  SCHEMAS = [{
    'burners': ("""CREATE TABLE burners(_id integer primary key autoincrement,
                phone_number_id text not null, voicemail_url text, user_id
                text not null, burner_id integer not null, name text, alias
                text, features text not null, total_minutes integer not null,
                expiration_date integer not null, date_created integer
                not null, last_updated_date integer, renewal_date integer
                default 0)"""),
    'connections': ("""CREATE TABLE connections(_id integer primary key
                    autoincrement, user_id integer not null, burner_id integer
                    not null, name text, service_name text not null)"""),
    'contacts': ("""CREATE TABLE contacts(_id integer primary key
                 autoincrement, contact_id text not null unique,
                 name text not null,
                 phone_number text not null, burner_id text, date_created
                 integer not null, last_updated_date integer not null)"""),
    'messages': ("""CREATE TABLE messages(_id integer primary key
                 autoincrement, message_id text not null unique,
                 contact_phone_number text
                 not null, message_type integer not null, contact_burner_id
                 text, voice_url text, date_created integer not null,
                 last_updated_date integer not null, user_id text not null,
                 sid text, burner_id text not null, duration integer)"""),
    'subscriptions': ("""CREATE TABLE subscriptions(_id integer primary key
                      autoincrement, subscription_id text not null unique, sku
                      text not null, burner_ids text, renewal_date integer,
                      burner_assigned_in_period integer, cancellation_date
                      integer)""")
  }]

  def ParseCommunicationInformationRow(self, parser_mediator, query, row,
                                       **unused_kwargs):
    """Parses a Communication Information record row.

      Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
      and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = AndroidCommunicationInformationEventData()
    event_data.phone_number_id = self._GetRowValue(query_hash, row,
                                                   'phone_number_id')
    event_data.voicemail_url = self._GetRowValue(query_hash, row,
                                                 'voicemail_url')
    event_data.user_id = self._GetRowValue(query_hash, row, 'user_id')
    event_data.name = self._GetRowValue(query_hash, row, 'name')
    event_data.alias = self._GetRowValue(query_hash, row, 'alias')
    event_data.features = self._GetRowValue(query_hash, row, 'features')
    event_data.total_minutes = self._GetRowValue(query_hash, row,
                                                 'total_minutes')
    event_data.expiration_date = self._GetRowValue(query_hash, row,
                                                   'expiration_date')
    event_data.date_created = self._GetRowValue(query_hash, row,
                                                'date_created')
    event_data.last_updated_date = self._GetRowValue(query_hash, row,
                                                     'last_updated_date')
    event_data.renewal_date = self._GetRowValue(query_hash, row,
                                                'renewal_date')

    parser_mediator.ProduceEventData(event_data)

sqlite.SQLiteParser.RegisterPlugin(AndroidCommunicationInformationPlugin)
