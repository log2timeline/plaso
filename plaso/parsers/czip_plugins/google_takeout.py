# -*- coding: utf-8 -*-
"""Compound ZIP parser plugin for Google Takeout dump files."""

from __future__ import unicode_literals

import base64
import copy
import email
import email.message
import json
import os
import re
import time

from datetime import datetime
from io import BytesIO
from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.parsers import czip
from plaso.parsers.czip_plugins import interface


class GoogleActivitiesEventData(events.EventData):
  """Google Activities event data.

  Attributes:
    header (str): activity name
    title (str): activity description
    titleUrl (str): url
    products (str): activity name or info about the activity

  """

  DATA_TYPE = 'web:google:activities'

  def __init__(self):
    """Initializes event data."""
    super(GoogleActivitiesEventData, self).__init__(data_type=self.DATA_TYPE)
    self.header = None
    self.title = None
    self.title_url = None
    self.subtitles = None
    self.details = None
    self.location = None

class GoogleGMailParserEventData(events.EventData):
  """MBox log event data.

  Attributes:
    mailfrom (str): sender
    mailto (str): recipient
    cc (str): secondary recipients
    bcc (str): names of tertiary recipients whose names are invisible
    subject (str): subject
    body (str): content of the email itself, written by the sender
    user_agent (str): user agent
    message_id (str): a unique string assigned by the mail system
      when the message is first created.
    received_by (str): MAC address, SMTP id and timestamp
    received_from (str): list of all the servers/computers through which
      the message traveled
    precedence (str): used to indicate that automated "vacation" or
      "out of office" responses should not be returned for this mail
    sender (str): address of the actual sender
    dkim_signature (str): email authentication method designed to detect
      email spoofing
    auth_results (str): trace header field where a receiver records the results
      of email authentication checks that it carried out
    ARC-Authentication-Results (str): a combination of an instance number and
      the results of the SPF, DKIM, and DMARC validation
    ARC-Seal (str): a combination of an instance number, a DKIM-like signature
      of the previous ARC-Seal headers, and the validity of
      the prior ARC entries.
    ARC-Message-Signature (str): a combination of an instance number and
      a DKIM-like signature of the entire message except for
      the ARC-Seal headers
    received_SPF (str): it stores results of SPF checks in more detail
      than Authentication-Results
    auto_submitted (str): it is used to mark automatically generated messages
    vbr_info (str): the domain name that is being certified
    in_reply_to (str): message-ID of the message that this is a reply to
    return_path (str): email address for return mail
  """

  DATA_TYPE = 'web:google:gmail'

  def __init__(self):
    """Initializes MBox event data."""
    super(GoogleGMailParserEventData, self).__init__(data_type=self.DATA_TYPE)
    self.mailfrom = None
    self.mailto = None
    self.cc = None
    self.bcc = None
    self.subject = None
    self.body = None
    self.user_agent = None
    self.message_id = None
    self.received_by = None
    self.received_from = None
    self.precedence = None
    self.sender = None
    self.received_spf = None
    self.vbr_info = None
    self.auth_results = None
    self.arc_seal = None
    self.arc_msg_signature = None
    self.arc_auth_results = None
    self.auto_submitted = None
    self.in_reply_to = None
    self.return_path = None

class GooglePurchasesEventData(events.EventData):
  """Google Purchases event data.

  Attributes:
    order id (str): order id
    merchant (str): seller
    status (str): purchase's status (Shipped, Cancelled ..)
    quantity (str): quantity
    price (str): price
    url (str): url
    address (str): destination point where the items is to be delivered

  """

  DATA_TYPE = 'web:google:purchases'

  def __init__(self):
    """Initializes event data."""
    super(GooglePurchasesEventData, self).__init__(data_type=self.DATA_TYPE)
    self.order_id = None
    self.merchant = None
    self.product = None
    self.status = None
    self.quantity = None
    self.price = None
    self.url = None
    self.address = None
    self.departure_airport = None
    self.arrival_airport = None


class GoogleHangoutsEventData(events.EventData):
  """Google Hangouts event data.

  Attributes:
    conversation id (str): conversation's id
    conversation type (str): conversation's type
    conversation medium (str): conversation's medium
    conversation view (str): conversation's view
    conversation name (str): conversation's name
    conversation old name (str): conversation's old name
    user (str): user
    user added (str): user added in a conversation
    user removed (str): user removed in a conversation
    inviter (str): user that invited someone in a conversation
    participant (str): user which is a participant in a conversation
    message text (str): message's text
    message photo (str): message's photo
    message type (str): message's type
  """

  DATA_TYPE = 'web:google:hangouts:messages'

  def __init__(self):
    """Initializes event data."""
    super(GoogleHangoutsEventData, self).__init__(data_type=self.DATA_TYPE)
    self.conversation_id = None
    self.conversation_name = None
    self.conversation_type = None
    self.conversation_notification_level = None
    self.conversation_view = None
    self.conversation_medium = None
    self.conversation_old_name = None
    self.user = None
    self.inviter = None
    self.participant = None
    self.user_added = None
    self.user_removed = None
    self.message_text = None
    self.message_photo = None
    self.message_type = None


class GoogleMapsEventData(events.EventData):
  """Google Maps event data.

  Attributes:
    latitude (float): latitude of the location.
    longitude (float): longitude of the location.
    accuracy (int): accuracy of the location, in meters.
    velocity (int): speed of the device at capture time
        (probably inferred based on other data points).
    heading (int): direction the device is traveling.
    altitude (int): altitude of the device (probably measured from sea level).
    vertical accuracy (int): accuracy of the vertical location of the device.
    activity (str): strings of activities in the format "TS,T,C-TS,T,C-..."
      where:
      - TS  is the timestamp of the activity.
      - T   is a machine learning magic to infer what the user is potentially
        doing.
      - C   is the confidence on T value.
      Example: "1540076351833,IN_VEHICLE,37-1540074430419,ON_FOOT,94-..."
  """

  DATA_TYPE = 'web:google:maps:location'

  def __init__(self):
    """Initializes event data."""
    super(GoogleMapsEventData, self).__init__(data_type=self.DATA_TYPE)
    self.latitude = None
    self.longitude = None
    self.accuracy = None
    self.velocity = None
    self.heading = None
    self.altitude = None
    self.vertical_accuracy = None
    self.activity = None


class GoogleChromeEventData(events.EventData):
  """Google Chrome History event data.

  Attributes:
    title (str): title of the visited page.
    url (str): URL where the visit originated from.
    client_id (str): id of the user device.
    page_transition (str): type of transitions between pages.
  """
  DATA_TYPE = 'web:google:chrome:history'

  def __init__(self):
    """Initializes event data."""
    super(GoogleChromeEventData, self).__init__(data_type=self.DATA_TYPE)
    self.title = None
    self.url = None
    self.client_id = None
    self.page_transition = None

class GoogleTakeoutPlugin(interface.CompoundZIPPlugin):
  """Parse metadata from Google Takeout dump files."""

  NAME = 'google_takeout'
  DESCRIPTION = 'Parser for Google Takeout dump files (JSON based).'

  def __init__(self):
    super(GoogleTakeoutPlugin, self).__init__()
    self._parser_mediator = None

  def InspectZipFile(self, parser_mediator, zip_file):
    """Parses a JSON-based Google Takeout dump file-like object.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
        and other components, such as storage and dfvfs.
      zip_file (zipfile): zipfile

    Raises:
      UnableToParseFile: when the file cannot be parsed.
    """

    self._parser_mediator = parser_mediator

    keys = {
        'lineItem': self._PurchasesParser,
        'locations': self._GmapsParser,
        'conversations': self._HangoutsParser,
        'Browser History': self._GchromeParser
    }

    for filepath in zip_file.namelist():
      filepath_encoded = filepath.encode('ascii', 'ignore')
      fp = filepath_encoded.decode('utf-8', 'replace')
      if fp.endswith('.json'):
        with zip_file.open(filepath) as f:
          json_data = json.loads(f.read())
          for key in keys:
            if key in json_data:
              getkey = keys[key]
              getkey(json_data, self._parser_mediator)
          for data in json_data:
            if 'header' and 'products' in data:
              self._ActivitiesParser(data, self._parser_mediator)
      elif filepath.endswith('.mbox'):
        mbox_file = BytesIO(zip_file.read(filepath))
        self._MBoxParser(mbox_file, self._parser_mediator)


  def CheckZipFile(self, zip_file, archive_members):
    """Checks if the zip file contains a file 'index.html';
       if so checks with regex the existence of the keyword 'Google Takeout'
       or 'Google Takeaway'.
       This keyword is in every Google's dump.

    Args:
      zip_file (zipfile.ZipFile): the zip file. It should not be closed in
          this method, but will be closed by the parser logic in czip.py.
      archive_members (list[str]): file paths in the archive.

    Returns:
      object: match between the first location and the pattern
    """

    if 'Takeout/index.html' in zip_file.namelist():
      with zip_file.open('Takeout/index.html') as f:
        data = f.read()
        takeout_regex = re.compile(
            r'<img\ssrc="data:image/png;base64,'
            r'((?:[A-Za-z0-9+/]{4})*(?:[A-Za-z0-9+/]{2}==|'
            r'[A-Za-z0-9+/]{3}=)?)"\salt="Google\sTake[a-z]{3,4}">')
        return re.search(takeout_regex, data)
    return False

  def _GetDateTime(self, date):
    """Gets the date time well formatted (Standard C asctime).
       The date time obtained is formatted as:
       (YYYY-MM-DD hh:mm:ss.######[+-]##:##)
       Where # are numeric digits ranging from 0 to 9 and the seconds
       fraction can be either 3 or 6 digits. Default time zone: UTC.
       It checks the sequence of character and it gets the time well
       formatted with the asctime pattern.
       There is a lookup table to replace the name of a month with its number.

       Args:
         date (str): date mail in asctime

       Returns:
         str: date mail well formatted
    """

    asctime_pattern = re.compile(
        r'(?P<day>\d{1,2})\s+'
        r'(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+'
        r'(?P<year>\d{4})\s+'
        r'(?P<hour>\d{1,2}):(?P<minute>\d{1,2}):(?P<second>\d{1,2})'
        r'(?:\s+(?P<timezone>[+-]\d{4}))?'
    )

    timezone_pattern = re.compile(r'([+-]\d{2})(\d{2})')

    month_lookup_table = {
        'Jan': 1, 'Feb': 2, 'Mar': 3,
        'Apr': 4, 'May': 5, 'Jun': 6,
        'Jul': 7, 'Aug': 8, 'Sep': 9,
        'Oct': 10, 'Nov': 11, 'Dec': 12
    }

    match = re.search(asctime_pattern, date)

    date_time_pattern = '{0:4s}-{1:02d}-{2:0>2s} ' \
    '{3:0>2s}:{4:0>2s}:{5:0>2s}.000{6}'

    time_string = date_time_pattern.format(
        match.group('year'),
        month_lookup_table[match.group('month')],
        match.group('day'), match.group('hour'),
        match.group('minute'),
        match.group('second'), re.sub(
            timezone_pattern, r'\1:\2',
            match.group('timezone') or '+0000'
        )
    )
    return time_string

  def _GetCharset(self, charset):
    """Checks with regex the message's charset

       Args:
         charset (str): charset

       Returns:
         str: charset
    """
    charset_pattern = r'([a-z]*/[a-z]*;\s)?(charset=)?\"?([a-z0-9\-_]+)\"?'
    match = re.search(
        charset_pattern,
        charset, re.IGNORECASE
    )
    if match.group(3):
      charset = match.group(3)
    return charset

  def _BodyMail(self, message):
    """Gets the body mail. If the body mail is encoded in Base64, it's decoded.

       Args:
         message (str): mail

       Returns:
         str: body mail
    """

    if (message.get_content_type() == 'text/plain') and \
      (message['Content-Transfer-Encoding'] == 'base64'):
      return base64.b64decode(message.get_payload())
    return message.get_payload()

  def _ParseBodyMail(self, mail):
    """Gets the mail content.
       A Message object consists of headers and payloads. The payload is
       either a string in the case of simple message objects or a list of
       Message objects for MIME container documents.
       For each message the charset is taken to do the right decoding.

       Args:
         mail (instance): mail

       Returns:
         str: plain-text mail body
    """

    charset = 'utf-8'
    body = ''
    if mail.is_multipart():
      for part in mail.walk():
        if part.is_multipart():
          for subpart in part.walk():
            if subpart.get_content_type() == 'text/plain':
              if subpart.get_charsets()[0]:
                if 'charset' in subpart.get_charsets()[0]:
                  charset = self._GetCharset(subpart.get_charsets()[0])
              body += self._BodyMail(subpart).decode(charset, 'ignore')
        else:
          if self._BodyMail(part):
            body = self._BodyMail(part)
    else:
      body = self._BodyMail(mail)
    return body

  # pylint: disable=invalid-name
  def _GetMailInfo(self, event_data, key, value):
    """Gets other mail info.
       There is dictionary mapping case values to functions to call.

    Args:
      event_data (GoogleGMailParserEventData): event data
      key (str): key
      value (str): value
    """

    keys = {
        'From': 'mailfrom',
        'To': 'mailto',
        'Cc': 'cc',
        'Bcc': 'bcc',
        'Subject': 'subject',
        'Precedence': 'precedence',
        'In-Reply-To': 'in_reply_to',
        'Authentication-Results': 'auth_results',
        'ARC-Seal': 'arc_seal',
        'ARC-Message-Signature': 'arc_msg_signature',
        'Received-SPF': 'received_spf',
        'Auto-Submitted': 'auto_submitted',
        'VBR-Info': 'vbr_info',
        'Return-Path': 'return_path'
    }

    if key in keys:
      setattr(event_data, keys[key], value)

  def _MBoxParser(self, file_object, parser_mediator):
    """Parses Mbox file (.mbox).

    Args:
      file_object (BytesIO): file-like
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
    """

    data = file_object.read(5)
    if not data.startswith('From '):
      display_name = parser_mediator.GetDisplayName()[3:]
      raise errors.UnableToParseFile(
          '[{0:s}] unable to parse file: {1:s} with error: {2:s}'.format(
              self.NAME, display_name, 'Not a MBox file.')
      )
    else:
      mail_box = Mbox(file_object)
      for mail in mail_box:
        event_data = GoogleGMailParserEventData()
        date_time = dfdatetime_time_elements.TimeElements()
        received_from = ''
        received_by = ''

        if 'Date' in mail.keys():
          for key, value in zip(mail.keys(), mail.values()):
            if key == 'Date':
              date_regex = re.compile(
                  r'([A-Za-z]{3},(\s){1,2})?[0-3]*[0-9]\s'
                  r'([A-Za-z]{3})?\s[1-2][0-9]{3}\s'
                  r'([0-9]|0[0-9]|1[0-9]|2[0-3]):[0-5][0-9]:[0-5][0-9]'
                  r'(\s[+-][0-9]{2}[0-9]{2})?'
                  r'(\s([(]?(([A-Z]{3})|([A-Z]{4}))[)])?)?'
              )
              if date_regex.match(str(value)):
                dt = self._GetDateTime(value)
                date_time.CopyFromDateTimeString(dt)
            elif key == 'Received':
              if value.startswith('by'):
                received_by = value + ' - ' + received_by
              if value.startswith('from'):
                received_from = 'hop (' \
                + value.replace('\n', '').replace('\t', '') \
                + ') ' + received_from
              event_data.received_by = received_by
              event_data.received_from = received_from
            else:
              self._GetMailInfo(event_data, key, value)

          event_data.body = self._ParseBodyMail(mail).decode('utf8', 'ignore')
          event = time_events.DateTimeValuesEvent(
              date_time, 'Mail')
          parser_mediator.ProduceEventWithEventData(event, event_data)

  def _GetSubtitles(self, datakey):
    """Gets subtitles (a secondary activity).

    Args:
      datakey (list): list of activities

    Returns:
      str: subtitles (a secondary activity)
    """

    subtitles = ''
    for subtitle in datakey:
      if 'name' in subtitle:
        if 'url' in subtitle:
          subtitles += subtitle['name'] + ': ' + subtitle['url']
        else:
          subtitles += subtitle['name'] + ' - '
      if 'url' in subtitle:
        subtitles += subtitle['url']
      return subtitles

  def _GetOtherActivities(self, event_data, data, key):
    """Gets secondary activities.

    Args:
      event_data (GoogleActivitiesEventData): event data
      data (dict): data of JSON file.
      key (unicode): data's key
    """

    if key == 'title':
      event_data.title = data[key]
    elif key == 'titleUrl':
      event_data.title_url = data[key]
    elif key == 'details':
      details = ''
      for detail in data[key]:
        details += detail['name']
      event_data.details = details
    elif key == 'subtitles':
      event_data.subtitles = self._GetSubtitles(data[key])[:-2]
    elif key == 'locations':
      event_data.location = data[key][0]['name'] + ': ' + data[key][0]['url']

  def _ActivitiesParser(self, data, parser_mediator):
    """Parses Activities file (JSON).

    Args:
      data (dict): data of JSON file.
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
    """

    event_data = GoogleActivitiesEventData()
    date_time = dfdatetime_time_elements.TimeElements()
    products = ''
    dt = ''
    header = ''

    for key in data:
      if key == 'header':
        header = data[key]
      elif key == 'products':
        for product in data[key]:
          products += product
        if header != products:
          event_data.header = header
      elif key == 'time':
        dt = data[key].replace('T', ' ').replace('Z', '')
        date_time.CopyFromDateTimeString(dt)
      else:
        self._GetOtherActivities(event_data, data, key)
    if dt:
      event = time_events.DateTimeValuesEvent(
          date_time, products
      )
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def _GetTimestampPurchase(self, ts):
    """Gets Purchase timestamp.

    Args:
      ts (unicode): timestamp from json

    Returns:
      PosixTimeInMicroseconds: timestamp in PosixTime
    """

    time_usec = ts
    timestamp = dfdatetime_posix_time.PosixTimeInMicroseconds(
        timestamp=time_usec
    )
    return timestamp

  # pylint: disable=unused-argument
  def _GetInfoFulfillmentPurchase(self, event_data, value, timestamp):

    """Gets info about fulfillment (purchase).

    Args:
      event_data (GoogleActivitiesEventData): event data
      value (str): value
      timestamp (unicode): timestamp from json

    """

    for el in value:
      if el == 'location':
        event_data.address = value[el] \
            ['address'][0]
      elif el == 'timeWindow':
        timestamp = self._GetTimestampPurchase(value[el]['startTime'] \
            ['usecSinceEpochUtc'])

  def _GetInfoAirportPurchase(self, event_data, value):
    """Gets info about Airport (purchase).

    Args:
      event_data (GoogleActivitiesEventData): event data
      value (str): value

    """
    for el in value:
      if el == 'departureAirport':
        event_data.departure_airport = value[el]['location']['name']
      if el == 'arrivalAirport':
        event_data.arrival_airport = value[el]['location']['name']

  # pylint: disable=unused-argument
  def _GetPurchaseInfo(self, event_data, value, info, timestamp):
    """Gets other Purchase info.

    Args:
      event_data (GoogleActivitiesEventData): event data
      value (str): value
      info (unicode): key
      timestamp (unicode): timestamp

    Returns:
      PosixTimeInMicroseconds: timestamp
    """

    def GetUnitPrice(value):
      """Gets and stores a value

      Args:
        value (unicode): value
      """
      for el in value:
        if el == 'displayString':
          event_data.price = value[el]

    def GetFulfillment(value):
      """Gets and stores a value using another method

      Args:
        value (unicode): value
      """
      self._GetInfoFulfillmentPurchase(event_data, value, timestamp)

    def GetFlightLeg(value):
      """Gets and stores a value using another method

      Args:
        value (unicode): value
      """
      self._GetInfoAirportPurchase(event_data, value)

    keys = {
        'status': 'status',
        'quantity': 'quantity',
        'productInfo': 'product',
        'landingPageUrl': 'url'
    }

    keys2 = {
        'unitPrice': GetUnitPrice,
        'fulfillment': GetFulfillment,
        'flightLeg': GetFlightLeg
    }

    if info in keys:
      if isinstance(value[info], dict):
        if 'link' in value[info]:
          setattr(event_data, keys[info], value[info]['link'])
        elif 'name' in value[info]:
          setattr(event_data, keys[info], value[info]['name'])
      else:
        setattr(event_data, keys[info], value[info])
    elif info in keys2:
      getKey = keys2[info]
      getKey(value[info])

    if info == 'bookingTimestamp':
      timestamp = self._GetTimestampPurchase(value[info]['usecSinceEpochUtc'])

    return timestamp

  def _PurchasesParser(self, data, parser_mediator):
    """Parses Purchases file (JSON).

    Args:
      data (dict): data of JSON file.
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
    """

    event_data = GooglePurchasesEventData()
    timestamp = ''
    for key in data:
      if key == 'merchantOrderId':
        event_data.order_id = data[key]
      elif key == 'transactionMerchant':
        event_data.merchant = data[key]['name']
      elif key == 'creationTime':
        timestamp = self._GetTimestampPurchase(data[key]['usecSinceEpochUtc'])
      elif key == 'lineItem':
        for element in data[key][0]:
          for info in data[key][0][element]:
            timestamp = self._GetPurchaseInfo(
                event_data, data[key][0][element], info, timestamp
            )

    if timestamp:
      event = time_events.DateTimeValuesEvent(timestamp, 'Purchase')
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def _GmapsParser(self, data, parser_mediator):
    """Parses Google Maps file (JSON).

    Args:
      data (dict): data of JSON file.
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
    """

    for location in data["locations"]:
      event_data = GoogleMapsEventData()
      date_time = dfdatetime_posix_time.PosixTimeInMilliseconds(
          timestamp=location["timestampMs"]
      )

      keys = {
          'latitudeE7': 'latitude',
          'longitudeE7': 'longitude',
          'velocity': 'velocity',
          'heading': 'heading',
          'altitude': 'altitude',
          'accuracy': 'accuracy',
          'verticalAccuracy': 'vertical_accuracy'
      }

      for key in location:
        if key in keys:
          if key == ('latitudeE7', 'longitudeE7'):
            setattr(event_data, keys[key], location[key] / 1e7)
          else:
            setattr(event_data, keys[key], location[key])

      if 'activity' in location:
        activity_str = ""
        for activity in location['activity']:
          timestamp_activity = datetime.fromtimestamp(
              int(activity['timestampMs']) // 1000
          )
          max_type = str(activity['activity'][0]['type'])
          max_confidence = int(activity['activity'][0]['confidence'])

          activity_str = activity_str + str(timestamp_activity) + "," \
          + max_type + "," + str(max_confidence) + "-"

        event_data.activity = activity_str[:-1]

      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_LOCATION_VISITED
      )
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def _GchromeParser(self, data, parser_mediator):
    """Parses Google Maps file (JSON).

    Args:
      data (dict): data of JSON file.
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
    """
    for page in data['Browser History']:
      date_time = dfdatetime_posix_time.PosixTimeInMicroseconds(
          timestamp=page['time_usec']
      )
      event_data = GoogleChromeEventData()
      event_data.title = page['title']
      event_data.url = page['url']
      event_data.client_id = page['client_id']
      event_data.page_transition = page['page_transition']
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_PAGE_VISITED
      )
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def _create_dict_users(self, data):
    """Creates a dictionary <User ID> : <User Name>.
       A dictionary is created to associate each id with a name.
       Without a dictionary some id would not have associated any names.

    Args:
      data (dict): data of JSON file.

    Returns:
      dict: dictionary <User ID> : <User Name>
    """

    users = dict()
    for comunication in data['conversations']:
      if ('conversation' in comunication) and (
          'participant_data' in comunication['conversation']['conversation']):
        for participant in \
            comunication['conversation']['conversation']['participant_data']:
          if ('id' in participant) and ('fallback_name' in participant):
            users[participant['id']['gaia_id']] = participant['fallback_name']
    return users

  def _GetConversationInfo(self, event_data, conversation):
    """Gets conversation's info

    Args:
      event_data (GoogleHangoutsEventData): event data
      conversation (dict): hangout conversation
    """
    event_data.conversation_id = conversation['id']['id']
    event_data.conversation_type = conversation['type']
    if 'name' in conversation:
      event_data.conversation_name = conversation['name']

  def _GetConversationState(self, event_data, conversation, users):
    """Get conversations' state

    Args:
      event_data (GoogleHangoutsEventData): event data
      conversation (dict): hangout conversation
      users (dict): list of users
    """

    event_data.conversation_notification_level = \
      conversation['notification_level']
    event_data.conversation_medium = conversation['view'][0]

    if 'inviter_id' in conversation:
      inviter = conversation['inviter_id']['gaia_id']
      inviter = str(users.get(inviter)) + ' (ID: ' + inviter + ')'
      event_data.inviter = inviter

  def _GetSegment(self, event_data, segments):
    """Get conversations' segment

    Args:
      event_data (GoogleHangoutsEventData): event data
      segments (dict): hangout attachment
    """
    for segment in segments:
      if 'type' in segment:
        event_data.message_type = segment['type']
      if 'text' in segment:
        event_data.message_text = event_data.message_text \
        + segment['text']

  def _GetAttachment(self, event_data, attachment):
    """Get conversations' attachment

    Args:
      event_data (GoogleHangoutsEventData): event data
      attachment (dict): hangout attachment
    """

    for item in attachment:
      event_data.message_type = item['embed_item']['type'][0]
      if 'plus_photo' in item['embed_item']:
        if 'thumbnail' in item['embed_item']['plus_photo']:
          event_data.message_photo = item['embed_item'] \
              ['plus_photo']['thumbnail']['image_url']

  def _GetMembershipChange(self, event_data, event, users):
    """Get conversations' membership change (join and leave).

    Args:
      event_data (GoogleHangoutsEventData): event data
      event (dict): event about a conversation's member
      users (dict): list of users
    """
    if event['type'] == 'JOIN':
      user_name = str(users.get(
          event['participant_id'][0]['gaia_id']
      ))
      event_data.user_added = user_name \
        + str(users.get(
            event['participant_id'][0]['gaia_id']
        ))
    elif event['type'] == 'LEAVE':
      event_data.user_removed = \
        str(users.get(
            event['participant_id'][0]['gaia_id']
        ))

  def _GetEventInfo(self, event, event_data, users):
    """Get Hangouts event info

    Args:
      event (dict): hangout evenet
      event_data (GoogleHangoutsEventData): event data
      users (dict): list of users
    """

    if 'conversation_id' in event:
      event_data.conversation_id = event['conversation_id']['id']
    if 'sender_id' in event:
      event_data.user = str(users.get(
          event['sender_id']['gaia_id']
      ))
    if ('chat_message' in event) and \
      ('message_content' in event['chat_message']):
      if 'segment' in event['chat_message']['message_content']:
        event_data.message_text = ''
        self._GetSegment(event_data, event['chat_message']['message_content'] \
            ['segment'])
      if 'attachment' in event['chat_message']['message_content']:
        self._GetAttachment(event_data, event['chat_message'] \
            ['message_content']['attachment'])
    if 'membership_change' in event:
      self._GetMembershipChange(event_data, event['membership_change'], users)
    if 'conversation_rename' in event:
      event_data.conversation_name = event['conversation_rename'] \
        ['new_name']
      event_data.conversation_old_name = event['conversation_rename'] \
        ['old_name']

  def _GetDefinitionEvent(self, event, event_data, users):
    definition = ''

    keys = {
        'ADD_USER': 'TIME_USER_ADDED',
        'REMOVE_USER': 'TIME_USER_REMOVED',
        'REGULAR_CHAT_MESSAGE': 'TIME_MESSAGE_SENT',
        'RENAME_CONVERSATION': 'TIME_CONVERSATION_RENAMED',
        'START_HANGOUT': 'Start Video Call',
        'END_HANGOUT': 'End Video Call'
    }

    if event['event_type'] in keys:
      definition = keys[event['event_type']]

    if event['event_type'] == 'HANGOUT_EVENT':
      if 'hangout_event' in event:
        participants = ''
        for participant in event['hangout_event']['participant_id']:
          participants = str(users.get(participant['gaia_id'])) \
          + ' (ID: ' + participant['gaia_id'] + '), ' + participants
        event_data.participant = participants[:-2]
        if event['hangout_event']['event_type'] in keys:
          definition = event['hangout_event']['event_type']
    return definition

  def _HangoutsParser(self, data, parser_mediator):
    """Parses Hangouts file (JSON).

    Args:
      data (dict): data of JSON file.
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
    """
    invite_ts_conv_event_data = GoogleHangoutsEventData()
    sort_ts_conv_event_data = GoogleHangoutsEventData()
    active_ts_conv_event_data = GoogleHangoutsEventData()
    latest_read_conv_event_data = GoogleHangoutsEventData()
    event_data = GoogleHangoutsEventData()

    users = self._create_dict_users(data)
    for comunication in data['conversations']:
      if ('conversation' in comunication) and ("events" in comunication):
        conversation = comunication['conversation']
        if 'conversation' in comunication['conversation']:
          self._GetConversationInfo(
              invite_ts_conv_event_data, conversation['conversation']
          )
          self._GetConversationInfo(
              sort_ts_conv_event_data, conversation['conversation']
          )
          self._GetConversationInfo(
              active_ts_conv_event_data, conversation['conversation']
          )
          self._GetConversationInfo(
              latest_read_conv_event_data, conversation['conversation']
          )

        if 'self_conversation_state' in conversation['conversation']:
          self_conversation_state = conversation['conversation']\
            ['self_conversation_state']
          if 'self_read_state' in self_conversation_state:
            self_read_state = self_conversation_state['self_read_state']
            if 'participant_id' in self_read_state:
              self_user = self_read_state['participant_id']['gaia_id']
            latest_read_conversation_timestamp = \
              dfdatetime_posix_time.PosixTimeInMicroseconds(
                  timestamp=self_read_state['latest_read_timestamp']
              )

          self._GetConversationState(
              invite_ts_conv_event_data, self_conversation_state, users
          )
          self._GetConversationState(
              sort_ts_conv_event_data, self_conversation_state, users
          )
          self._GetConversationState(
              active_ts_conv_event_data, self_conversation_state, users
          )
          self._GetConversationState(
              latest_read_conv_event_data, self_conversation_state, users
          )

          if 'invite_timestamp' in self_conversation_state:
            invite_conversation_timestamp = \
              dfdatetime_posix_time.PosixTimeInMicroseconds(
                  timestamp=self_conversation_state['invite_timestamp']
              )
            event_invite_ts_conversation = time_events.DateTimeValuesEvent(
                invite_conversation_timestamp,
                'Invitation Conversation'
            )
          if 'sort_timestamp' in self_conversation_state:
            sort_conversation_timestamp = \
              dfdatetime_posix_time.PosixTimeInMicroseconds(
                  timestamp=self_conversation_state['sort_timestamp']
              )
            event_sort_ts_conversation = time_events.DateTimeValuesEvent(
                sort_conversation_timestamp,
                'Sorting Conversation'
            )
          if 'active_timestamp' in self_conversation_state:
            active_conversation_timestamp = \
              dfdatetime_posix_time.PosixTimeInMicroseconds(
                  timestamp=self_conversation_state['active_timestamp']
              )
            event_active_ts_conversation = time_events.DateTimeValuesEvent(
                active_conversation_timestamp,
                'Activation Conversation'
            )
          latest_read_conversation = time_events.DateTimeValuesEvent(
              latest_read_conversation_timestamp, definitions.TIME_LATEST_READ
          )

        latest_read_conv_event_data.user = str(users.get(self_user)) \
          + ' (ID: ' + self_user + ')'

        parser_mediator.ProduceEventWithEventData(
            event_invite_ts_conversation, invite_ts_conv_event_data
        )
        parser_mediator.ProduceEventWithEventData(
            event_sort_ts_conversation, sort_ts_conv_event_data
        )
        parser_mediator.ProduceEventWithEventData(
            event_active_ts_conversation, active_ts_conv_event_data
        )
        parser_mediator.ProduceEventWithEventData(
            latest_read_conversation, latest_read_conv_event_data
        )

        for event in comunication['events']:
          event_data = GoogleHangoutsEventData()
          self._GetEventInfo(event, event_data, users)
          message_timestamp = dfdatetime_posix_time.PosixTimeInMicroseconds(
              timestamp=event['timestamp']
          )

          definition = self._GetDefinitionEvent(event, event_data, users)
          date_time_message = time_events.DateTimeValuesEvent(
              message_timestamp, definition
          )
          parser_mediator.ProduceEventWithEventData(
              date_time_message, event_data
          )

# pylint: disable=bad-option-value
# pylint: disable=old-style-class
# pylint: disable=abstract-method
class Mailbox:
  """A group of messages in a particular place."""

  # pylint: disable=unused-argument
  def __init__(self, factory=None, create=True):
    """Initialize a Mailbox instance."""
    self._factory = factory

  def __setitem__(self, key, message):
    """Replace the keyed message; raise KeyError if it doesn't exist."""
    raise NotImplementedError('Method must be implemented by subclass')

  def Get(self, key, default=None):
    """Return the keyed message, or default if it doesn't exist."""
    try:
      return self.__getitem__(key)
    except KeyError:
      return default

  def __getitem__(self, key):
    """Return the keyed message; raise KeyError if it doesn't exist."""
    if not self._factory:
      return self.Get_message(key)
    return KeyError('No message with key: %s' % key)

  def Get_message(self, key):
    """Return a Message representation or raise a KeyError."""
    raise NotImplementedError('Method must be implemented by subclass')

  def Iterkeys(self):
    """Return an iterator over keys."""
    raise NotImplementedError('Method must be implemented by subclass')

  # pylint: disable=invalid-name
  def keys(self):
    """Return a list of keys."""
    return list(self.Iterkeys())

  def Itervalues(self):
    """Return an iterator over all messages."""
    for key in self.Iterkeys():
      try:
        value = self[key]
      except KeyError:
        continue
      yield value

  def __iter__(self):
    return self.Itervalues()

  # pylint: disable=invalid-name
  def values(self):
    """Return a list of messages. Memory intensive."""
    return list(self.Itervalues())

  def Iteritems(self):
    """Return an iterator over (key, message) tuples."""
    for key in self.Iterkeys():
      try:
        value = self[key]
      except KeyError:
        continue
      yield (key, value)

  def Items(self):
    """Return a list of (key, message) tuples. Memory intensive."""
    return list(self.Iteritems())

  def __len__(self):
    """Return a count of messages in the mailbox."""
    raise NotImplementedError('Method must be implemented by subclass')

  # Whether each message must end in a newline
  _append_newline = False


class _singlefileMailbox(Mailbox):
  """A single-file mailbox."""

  def __init__(self, file_object, factory=None, create=True):
    """Initialize a single-file mailbox."""
    Mailbox.__init__(self, factory, create)
    self._file = file_object
    self._toc = None
    self._next_key = 0
    self._pending = False       # No changes require rewriting the file.
    self._file_length = None    # Used to record mailbox size

  def __setitem__(self, key, message):
    """Replace the keyed message; raise KeyError if it doesn't exist."""
    self._lookup(key)
    self._pending = True

  def Iterkeys(self):
    """Return an iterator over keys."""
    self._lookup()
    for key in self._toc.keys():
      yield key

  def __len__(self):
    """Return a count of messages in the mailbox."""
    self._lookup()
    return len(self._toc)

  def _lookup(self, key=None):
    """Return (start, stop) or raise KeyError."""
    if self._toc is None:
      # pylint: disable=maybe-no-member
      self._generate_toc()
    if key is not None:
      try:
        return self._toc[key]
      except KeyError:
        raise KeyError('No message with key: %s' % key)
    return KeyError('No message with key: %s' % key)

class _mboxMMDF(_singlefileMailbox):
  """An mbox or MMDF mailbox."""

  _mangle_from_ = True

  def Get_message(self, key):
    """Return a Message representation or raise a KeyError."""
    start, stop = self._lookup(key)
    self._file.seek(start)
    from_line = self._file.readline().replace(os.linesep, b'')
    string = self._file.read(stop - self._file.tell())
    # pylint: disable=maybe-no-member
    msg = self._message_factory(string.replace(os.linesep, b'\n'))
    msg.Set_from(from_line[5:])
    return msg

class Mbox(_mboxMMDF):
  """A classic mbox mailbox."""

  _mangle_from_ = True
  _append_newline = True

  def __init__(self, file_object, factory=None, create=True):
    """Initialize an mbox mailbox."""

    self._message_factory = MboxMessage
    _mboxMMDF.__init__(self, file_object, factory, create)

  def _generate_toc(self):
    """Generate key-to-(start, stop) table of contents."""
    starts, stops = [], []
    last_was_empty = False
    self._file.seek(0)

    while True:
      line_pos = self._file.tell()
      line = self._file.readline()
      if line.startswith(b'From '):
        if len(stops) < len(starts):
          if last_was_empty:
            stops.append(line_pos - len(os.linesep))
          else:
            stops.append(line_pos)
        starts.append(line_pos)
        last_was_empty = False
      elif not line:
        if last_was_empty:
          stops.append(line_pos - len(os.linesep))
        else:
          stops.append(line_pos)
        break
      elif line == os.linesep:
        last_was_empty = True
      else:
        last_was_empty = False

    self._toc = dict(enumerate(zip(starts, stops)))
    self._next_key = len(self._toc)
    self._file_length = self._file.tell()

class Message(email.message.Message):
  """Message with mailbox-format-specific properties."""

  def __init__(self, message=None):
    """Initialize a Message instance."""
    if isinstance(message, email.message.Message):
      self._become_message(copy.deepcopy(message))
      if isinstance(message, Message):
        # pylint: disable=protected-access
        message._explain_to(self)
    elif isinstance(message, str):
      self._become_message(email.message_from_string(message))
    elif hasattr(message, "read"):
      self._become_message(email.message_from_file(message))
    elif message is None:
      email.message.Message.__init__(self)
    else:
      raise TypeError('Invalid message type: %s' % type(message))

  def _become_message(self, message):
    """Assume the non-format-specific state of message."""
    for name in ('_headers', '_unixfrom', '_payload', '_charset',
                 'preamble', 'epilogue', 'defects', '_default_type'):
      self.__dict__[name] = message.__dict__[name]

class _mboxMMDFMessage(Message):
  """Message with mbox- or MMDF-specific properties."""

  def __init__(self, message=None):
    """Initialize an mboxMMDFMessage instance."""
    self.Set_from('MAILER-DAEMON', True)
    if isinstance(message, email.message.Message):
      unixfrom = message.get_unixfrom()
      if unixfrom is not None and unixfrom.startswith('From '):
        self.Set_from(unixfrom[5:])
    Message.__init__(self, message)

  def Get_from(self):
    """Return contents of "From " line."""
    return self._from

  def Set_from(self, from_, time_=None):
    """Set "From " line, formatting and appending time_ if specified."""
    if time_ is not None:
      if time_ is True:
        time_ = time.gmtime()
      from_ += ' ' + time.asctime(time_)
    self._from = from_

class MboxMessage(_mboxMMDFMessage):
  """Message with mbox-specific properties."""

class MMDFMessage(_mboxMMDFMessage):
  """Message with MMDF-specific properties."""

class Error(Exception):
  """Raised for module-specific errors."""

class NoSuchMailboxError(Error):
  """The specified mailbox does not exist and won't be created."""

class NotEmptyError(Error):
  """The specified mailbox is not empty and deletion was requested."""

class ExternalClashError(Error):
  """Another process caused an action to fail."""

class FormatError(Error):
  """A file appears to have an invalid format."""

czip.CompoundZIPParser.RegisterPlugin(GoogleTakeoutPlugin)
