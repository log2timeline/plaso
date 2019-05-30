# -*- coding: utf-8 -*-
"""This file contains the Popularity Contest log file parser in plaso.

Information updated 20 january 2014.
From Debian Package Popularity Contest
Avery Pennarun <apenwarr@debian.org>

From  'http://www.unix.com/man-page/Linux/8/popularity-contest/':

    The  popularity-contest command gathers information about Debian pack-
    ages installed on the system, and prints the name of the most  recently
    used  executable  program  in that package as well as its last-accessed
    time (atime) and last-attribute-changed time (ctime) to stdout.

    When aggregated with the output of popularity-contest from  many  other
    systems,  this information is valuable because it can be used to deter-
    mine which Debian packages are commonly installed, used,  or  installed
    and  never  used.  This helps Debian maintainers make decisions such as
    which packages should be installed by default on new systems.

    The resulting  statistic  is  available  from  the  project  home  page
    http://popcon.debian.org/.

    Normally,    popularity-contest    is   run   from   a cron(8)   job,
    /etc/cron.daily/popularity-contest,  which  automatically  submits  the
    results  to  Debian package maintainers (only once a week) according to
    the settings in /etc/popularity-contest.conf and /usr/share/popularity-
    contest/default.conf.


From 'http://popcon.ubuntu.com/README':

The popularity-contest output looks like this:

    POPULARITY-CONTEST-0 TIME:914183330 ID:b92a5fc1809d8a95a12eb3a3c8445
    914183333 909868335 grep /bin/fgrep
    914183333 909868280 findutils /usr/bin/find
    914183330 909885698 dpkg-awk /usr/bin/dpkg-awk
    914183330 909868577 gawk /usr/bin/gawk
    [...more lines...]
    END-POPULARITY-CONTEST-0 TIME:914183335

    The first and last lines allow you to put more than one set of
    popularity-contest results into a single file and then split them up
    easily later.

    The rest of the lines are package entries, one line for each package
    installed on your system.  They have the format:

    <atime> <ctime> <package-name> <mru-program> <tag>

    <package-name> is the name of the Debian package that contains
    <mru-program>. <mru-program> is the most recently used program,
    static library, or header (.h) file in the package.

    <atime> and <ctime> are the access time and creation time of the
    <mru-program> on your disk, respectively, represented as the number of
    seconds since midnight GMT on January 1, 1970 (i.e. in Unix time_t format).
    Linux updates <atime> whenever you open the file; <ctime> was set when you
    first installed the package.

    <tag> is determined by popularity-contest depending on <atime>, <ctime>, and
    the current date.  <tag> can be RECENT-CTIME, OLD, or NOFILES.

    RECENT-CTIME means that atime is very close to ctime; it's impossible to
    tell whether the package was used recently or not, since <atime> is also
    updated when <ctime> is set.  Normally, this happens because you have
    recently upgraded the package to a new version, resetting the <ctime>.

    OLD means that the <atime> is more than a month ago; you haven't used the
    package for more than a month.

    NOFILES means that no files in the package seemed to be programs, so
    <atime>, <ctime>, and <mru-program> are invalid.'

   REMARKS. The parser will generate events solely based on the <atime> field
   and not using <ctime>, to reduce the generation of (possibly many) useless
   events all with the same <ctime>. Indeed, that <ctime> will be probably
   get from file system and/or package management logs. The <ctime> will be
   reported in the log line.
"""

from __future__ import unicode_literals

import pyparsing

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.containers import time_events
from plaso.lib import definitions
from plaso.lib import errors
from plaso.lib import py2to3
from plaso.parsers import logger
from plaso.parsers import manager
from plaso.parsers import text_parser


class PopularityContestSessionEventData(events.EventData):
  """Popularity Contest session event data.

  Attributes:
    details (str): version and host architecture.
    hostid (str): host uuid.
    session (int): session number.
    status (str): session status, either "start" or "end".
  """

  DATA_TYPE = 'popularity_contest:session:event'

  def __init__(self):
    """Initializes event data."""
    super(PopularityContestSessionEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.details = None
    self.hostid = None
    self.session = None
    self.status = None


class PopularityContestEventData(events.EventData):
  """Popularity Contest event data.

  Attributes:
    mru (str): recently used app/library from package.
    package (str): installed packaged name, which the mru belongs to.
    record_tag (str): popularity context tag.
  """

  DATA_TYPE = 'popularity_contest:log:event'

  def __init__(self):
    """Initializes event data."""
    super(PopularityContestEventData, self).__init__(data_type=self.DATA_TYPE)
    self.mru = None
    self.package = None
    self.record_tag = None


class PopularityContestParser(text_parser.PyparsingSingleLineTextParser):
  """Parse popularity contest log files."""

  NAME = 'popularity_contest'
  DESCRIPTION = 'Parser for popularity contest log files.'

  _ASCII_PRINTABLES = pyparsing.printables
  _UNICODE_PRINTABLES = ''.join(
      py2to3.UNICHR(character) for character in range(65536)
      if not py2to3.UNICHR(character).isspace())

  MRU = pyparsing.Word(_UNICODE_PRINTABLES).setResultsName('mru')
  PACKAGE = pyparsing.Word(_ASCII_PRINTABLES).setResultsName('package')
  TAG = pyparsing.QuotedString('<', endQuoteChar='>').setResultsName('tag')

  HEADER = (
      pyparsing.Literal('POPULARITY-CONTEST-').suppress() +
      text_parser.PyparsingConstants.INTEGER.setResultsName('session') +
      pyparsing.Literal('TIME:').suppress() +
      text_parser.PyparsingConstants.INTEGER.setResultsName('timestamp') +
      pyparsing.Literal('ID:').suppress() +
      pyparsing.Word(pyparsing.alphanums, exact=32).setResultsName('id') +
      pyparsing.SkipTo(pyparsing.LineEnd()).setResultsName('details'))

  FOOTER = (
      pyparsing.Literal('END-POPULARITY-CONTEST-').suppress() +
      text_parser.PyparsingConstants.INTEGER.setResultsName('session') +
      pyparsing.Literal('TIME:').suppress() +
      text_parser.PyparsingConstants.INTEGER.setResultsName('timestamp'))

  LOG_LINE = (
      text_parser.PyparsingConstants.INTEGER.setResultsName('atime') +
      text_parser.PyparsingConstants.INTEGER.setResultsName('ctime') +
      (PACKAGE + TAG | PACKAGE + MRU + pyparsing.Optional(TAG)))

  LINE_STRUCTURES = [
      ('logline', LOG_LINE),
      ('header', HEADER),
      ('footer', FOOTER),
  ]

  _SUPPORTED_KEYS = frozenset([key for key, _ in LINE_STRUCTURES])

  _ENCODING = 'UTF-8'

  def _ParseLogLine(self, parser_mediator, structure):
    """Extracts events from a log line.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      structure (pyparsing.ParseResults): structure parsed from the log file.
    """
    # Required fields are <mru> and <atime> and we are not interested in
    # log lines without <mru>.
    mru = self._GetValueFromStructure(structure, 'mru')
    if not mru:
      return

    event_data = PopularityContestEventData()
    event_data.mru = mru
    event_data.package = self._GetValueFromStructure(structure, 'package')
    event_data.record_tag = self._GetValueFromStructure(structure, 'tag')

    # The <atime> field (as <ctime>) is always present but could be 0.
    # In case of <atime> equal to 0, we are in <NOFILES> case, safely return
    # without logging.
    access_time = self._GetValueFromStructure(structure, 'atime')
    if access_time:
      # TODO: not doing any check on <tag> fields, even if only informative
      # probably it could be better to check for the expected values.
      date_time = dfdatetime_posix_time.PosixTime(timestamp=access_time)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_LAST_ACCESS)
      parser_mediator.ProduceEventWithEventData(event, event_data)

    change_time = self._GetValueFromStructure(structure, 'ctime')
    if change_time:
      date_time = dfdatetime_posix_time.PosixTime(timestamp=change_time)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_ENTRY_MODIFICATION)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def ParseRecord(self, parser_mediator, key, structure):
    """Parses a log record structure and produces events.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): structure parsed from the log file.

    Raises:
      ParseError: when the structure type is unknown.
    """
    if key not in self._SUPPORTED_KEYS:
      raise errors.ParseError(
          'Unable to parse record, unknown structure: {0:s}'.format(key))

    # TODO: Add anomaly objects for abnormal timestamps, such as when the log
    # timestamp is greater than the session start.
    if key == 'logline':
      self._ParseLogLine(parser_mediator, structure)

    else:
      timestamp = self._GetValueFromStructure(structure, 'timestamp')
      if timestamp is None:
        logger.debug('[{0:s}] {1:s} with invalid timestamp.'.format(
            self.NAME, key))
        return

      session = self._GetValueFromStructure(structure, 'session')

      event_data = PopularityContestSessionEventData()
      # TODO: determine why session is formatted as a string.
      event_data.session = '{0!s}'.format(session)

      if key == 'header':
        event_data.details = self._GetValueFromStructure(structure, 'details')
        event_data.hostid = self._GetValueFromStructure(structure, 'id')
        event_data.status = 'start'

      elif key == 'footer':
        event_data.status = 'end'

      date_time = dfdatetime_posix_time.PosixTime(timestamp=timestamp)
      event = time_events.DateTimeValuesEvent(
          date_time, definitions.TIME_DESCRIPTION_ADDED)
      parser_mediator.ProduceEventWithEventData(event, event_data)

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a Popularity Contest log file.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfvfs.
      line (str): line from a text file.

    Returns:
      bool: True if the line was successfully parsed.
    """
    try:
      self.HEADER.parseString(line)
    except pyparsing.ParseException:
      logger.debug('Not a Popularity Contest log file, invalid header')
      return False

    return True


manager.ParsersManager.RegisterParser(PopularityContestParser)
