# -*- coding: utf-8 -*-
"""Google Takeout event formatter."""

from __future__ import unicode_literals

from plaso.formatters import interface
from plaso.formatters import manager

class GoogleGmailUpdateEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for MBox event."""

  DATA_TYPE = 'web:google:gmail'

  FORMAT_STRING_PIECES = [
      'From: {mailfrom}',
      'To: {mailto}',
      'Message id: {message_id}',
      'Cc: {cc}',
      'Bcc: {bcc}',
      'Subject: {subject}',
      'Body: {body}',
      'User Agent: {user_agent}',
      'Received by: {received_by}',
      'Received from: {received_from}',
      'Precedence: {precedence}',
      'Sender: {sender}',
      'Received SPF: {received_spf}',
      'VBR Info: {vbr_info}',
      'Authentication results: {auth_results}',
      'ARC-Seal: {arc_seal}',
      'ARC-Message-Signature: {arc_msg_signature}',
      'ARC-Authentication-Results: {arc_auth_results}',
      'Auto submitted: {auto_submitted}',
      'In reply to: {in_reply_to}',
      'Return path: {return_path}']

  FORMAT_STRING_SEPARATOR = '; '

  SOURCE_LONG = 'MBox mail'
  SOURCE_SHORT = 'MBOX'


class GoogleActivitiesUpdateEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for an activity event."""

  DATA_TYPE = 'web:google:activities'

  SOURCE_LONG = 'Google Activities Takeout'
  SOURCE_SHORT = 'GOOGLE_TAKEOUT'

  FORMAT_STRING_SEPARATOR = '; '

  FORMAT_STRING_PIECES = [
      'Header: {header}',
      'Title: {title}',
      'TitleURL: {title_url}',
      'Subtitles: {subtitles}',
      'Details: {details}',
      'Location: {location}'
  ]

class GooglePurchasesUpdateEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a purchase event."""

  DATA_TYPE = 'web:google:purchases'

  SOURCE_LONG = 'Google Purchases Takeout'
  SOURCE_SHORT = 'GOOGLE_TAKEOUT'

  FORMAT_STRING_SEPARATOR = '; '

  FORMAT_STRING_PIECES = [
      'Order ID: {order_id}',
      'Merchant: {merchant}',
      'Product: {product}',
      'Status: {status}',
      'Quantity: {quantity}',
      'Price: {price}',
      'Url: {url}',
      'Address: {address}',
      'Departure Airport: {departure_airport}',
      'Arrival Airport: {arrival_airport}'
  ]

class GoogleMapsUpdateEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Google Maps location event."""

  DATA_TYPE = 'web:google:maps:location'

  SOURCE_LONG = 'Google Maps Takeout'
  SOURCE_SHORT = 'GOOGLE_TAKEOUT'

  FORMAT_STRING_SEPARATOR = '; '

  FORMAT_STRING_PIECES = [
      'Latitude: {latitude}',
      'Longitude: {longitude}',
      'Accuracy: {accuracy}',
      'Velocity: {velocity}',
      'Heading: {heading}',
      'Altitude: {altitude}',
      'Vertical accuracy: {vertical_accuracy}',
      'Activity: {activity}'
  ]


class GoogleChromeHistoryUpdateEventFormatter(
    interface.ConditionalEventFormatter):
  """Formatter for a Google Chrome history event."""
  DATA_TYPE = 'web:google:chrome:history'

  SOURCE_LONG = 'Google Chrome History Takeout'
  SOURCE_SHORT = 'GOOGLE_TAKEOUT'

  FORMAT_STRING_SEPARATOR = '; '

  FORMAT_STRING_PIECES = [
      'Title: {title}',
      'URL: {url}',
      'Client ID: {client_id}',
      'Page Transition: {page_transition}',
  ]

class GoogleHangoutsUpdateEventFormatter(interface.ConditionalEventFormatter):
  """Formatter for a Google Hangouts event."""
  DATA_TYPE = 'web:google:hangouts:messages'

  SOURCE_LONG = 'Google Hangouts Takeout'
  SOURCE_SHORT = 'GOOGLE_TAKEOUT'

  FORMAT_STRING_SEPARATOR = '; '

  FORMAT_STRING_PIECES = [
      'Conversation ID: {conversation_id}',
      'Conversation name: {conversation_name}',
      'Conversation type: {conversation_type}',
      'Conversation view: {conversation_view}',
      'Conversation medium: {conversation_medium}',
      'User: {user}',
      'Inviter: {inviter}',
      'Participant: {participant}',
      'Message type: {message_type}',
      'Message text: {message_text}',
      'Message photo: {message_photo}',
      'Conversation old name: {conversation_old_name}',
      'User added: {user_added}',
      'User removed: {user_removed}'
  ]

manager.FormattersManager.RegisterFormatter(
    GoogleGmailUpdateEventFormatter)

manager.FormattersManager.RegisterFormatter(
    GoogleActivitiesUpdateEventFormatter)

manager.FormattersManager.RegisterFormatter(
    GooglePurchasesUpdateEventFormatter)

manager.FormattersManager.RegisterFormatter(
    GoogleMapsUpdateEventFormatter)

manager.FormattersManager.RegisterFormatter(
    GoogleChromeHistoryUpdateEventFormatter)

manager.FormattersManager.RegisterFormatter(
    GoogleHangoutsUpdateEventFormatter)
