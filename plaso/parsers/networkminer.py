
# -*- coding: utf-8 -*-
"""Parser for NetworkMiner output files."""

from __future__ import unicode_literals

import csv
from dfdatetime import definitions as dfdatetime_definitions
from dfdatetime import posix_time as dfdatetime_posix_time
from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import errors
from plaso.lib import definitions
from plaso.lib import py2to3
from plaso.formatters import trendmicroav as formatter
from plaso.parsers import dsv_parser
from plaso.parsers import manager
import logging
import pdb

class NetworkMinerEventData(events.EventData):
	"""NetworkMiner event Data.

	Attributes:
	source_ip (str): Originating IP address.
	source_port (str): Originating port number.
	destination_ip (str): Destination IP address.
	destination_port (str): Destination port number.
	time_stamp (dfdatetime): time 
	filename (string): Name of the file.
	file_path (string): File path to where it was downloaded.
	file_size (string): Size of the file.
	file_md5 (string): MD5 hash of the file.
	file_details (string): Details about the file.
	"""
	DATA_TYPE = "scanner:networkminer:fileinfos" 

	def __init__(self):
		super(NetworkMinerEventData, self).__init__()
		self.source_ip = None
		self.source_port = None
		self.destination_ip = None
		self.destination_port = None
		self.filename = None
		self.file_path = None
		self.file_size = None
		self.file_md5 = None
		self.file_details = None

class NetworkMinerParser(dsv_parser.DSVParser):
	"""Parser class for networkminer fileinfos."""
	
	NAME = 'networkminer_fileinfo'
	DESCRIPTION = 'Parser for NetworkMiner .fileinfos csv.'

	COLUMNS = (
		'source_ip', 'source_port', 'destination_ip', 'destination_port', 
		'filename', 'file_path','file_size', 'unused', 'file_md5', 'unused2',
		'unused3', 'unused4', 'timestamp')

	MIN_COLUMNS = 13

	def ParseRow (self, parser_mediator, row_offset, row):
		"""Parses a line of the log file and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row_offset (int): line number of the row.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.
    """
		event_data = NetworkMinerEventData()
		date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
		
		
		if row.get('timestamp', None) != "Timestamp":
			for field in ('source_ip', 'source_port', 'destination_ip', 'destination_port', 
	      'filename', 'file_path', 'file_size', 'file_md5'):
				setattr(event_data, field, row[field])
		

			try:
				#pdb.set_trace()
				timestamp = row.get('timestamp', None)
				#time = time[:27]+time[27:]
				logging.error('time is %s',(timestamp))
			
				timestamp = date_time.CopyFromStringISO8601(timestamp)
				logging.error('returned %s', timestamp)
			except ValueError:
				logging.error('afsf')
				parser_mediator.ProduceExtractionWarning(
			      'invalid date time value')
				return
			event = time_events.DateTimeValuesEvent(
			timestamp, definitions.TIME_DESCRIPTION_WRITTEN)
			parser_mediator.ProduceEventWithEventData(event, event_data)
	def VerifyRow(self, parser_mediator, row):
		"""Verifies if a line of the file is in the expected format.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      row (dict[str, str]): fields of a single row, as specified in COLUMNS.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
		logging.error(len(row))
		logging.error(self.MIN_COLUMNS)
		if len(row) != self.MIN_COLUMNS:
			return False

		return True
    # Check the date format!
    # If it doesn't parse, then this isn't a Trend Micro AV log.
		# date_time = dfdatetime_time_elements.TimeElementsInMicroseconds()
		# try:
		# 	date_time.CopyFromStringISO8601(row.get('timestamp', None))
		# except ValueError:
		#   return False

   
manager.ParsersManager.RegisterParser(NetworkMinerParser)


		