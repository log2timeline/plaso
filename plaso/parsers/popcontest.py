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

import logging

import pyparsing

from plaso.events import time_events
from plaso.lib import eventdata
from plaso.lib import timelib
from plaso.parsers import manager
from plaso.parsers import text_parser


__author__ = 'Francesco Picasso (francesco.picasso@gmail.com)'


class PopularityContestSessionEvent(time_events.PosixTimeEvent):
  """Convenience class for a Popularity Contest start/end event."""

  DATA_TYPE = 'popularity_contest:session:event'

  def __init__(self, timestamp, session, status, hostid=None, details=None):
    """Initializes the event object.

    Args:
      timestamp: microseconds since epoch in UTC, it's the start/end time.
      session: the session number.
      status: start or end of the session.
      hostid: the host uuid.
      details: the popularity contest version and host architecture.
    """
    super(PopularityContestSessionEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ADDED_TIME)
    self.session = session
    self.status = status
    self.hostid = hostid
    self.details = details


class PopularityContestEvent(time_events.PosixTimeEvent):
  """Convenience class for a Popularity Contest line event."""

  DATA_TYPE = 'popularity_contest:log:event'

  def __init__(self, timestamp, ctime, package, mru, tag=None):
    """Initializes the event object.

    Args:
      timestamp: microseconds since epoch in UTC, it's the <atime>.
      ctime: seconds since epoch in UTC, it's the <ctime>.
      package: the installed packaged name, whom mru belongs to.
      mru: the recently used app/library from package.
      tag: the popularity context tag.
    """
    super(PopularityContestEvent, self).__init__(
        timestamp, eventdata.EventTimestamp.ACCESS_TIME)
    # TODO: adding ctime as is, reconsider a conversion to human readable form.
    self.ctime = ctime
    self.package = package
    self.mru = mru
    self.record_tag = tag


class PopularityContestParser(text_parser.PyparsingSingleLineTextParser):
  """Parse popularity contest log files."""

  NAME = 'popularity_contest'
  DESCRIPTION = u'Parser for popularity contest log files.'

  EPOCH = text_parser.PyparsingConstants.INTEGER.setResultsName('epoch')
  PACKAGE = pyparsing.Word(pyparsing.printables).setResultsName('package')
  MRU = pyparsing.Word(pyparsing.printables).setResultsName('mru')
  TAG = pyparsing.QuotedString('<', endQuoteChar='>').setResultsName('tag')

  HEADER = (
      pyparsing.Literal(u'POPULARITY-CONTEST-').suppress() +
      text_parser.PyparsingConstants.INTEGER.setResultsName('session') +
      pyparsing.Literal(u'TIME:').suppress() + EPOCH +
      pyparsing.Literal('ID:').suppress() +
      pyparsing.Word(pyparsing.alphanums, exact=32).setResultsName('id') +
      pyparsing.SkipTo(pyparsing.LineEnd()).setResultsName('details'))

  FOOTER = (
      pyparsing.Literal(u'END-POPULARITY-CONTEST-').suppress() +
      text_parser.PyparsingConstants.INTEGER.setResultsName('session') +
      pyparsing.Literal(u'TIME:').suppress() + EPOCH)

  LOG_LINE = (
      EPOCH.setResultsName('atime') + EPOCH.setResultsName('ctime') +
      (PACKAGE + TAG | PACKAGE + MRU + pyparsing.Optional(TAG)))

  LINE_STRUCTURES = [
      ('logline', LOG_LINE),
      ('header', HEADER),
      ('footer', FOOTER),
  ]

  def VerifyStructure(self, parser_mediator, line):
    """Verify that this file is a Popularity Contest log file.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      line: A single line from the text file.

    Returns:
      True if this is the correct parser, False otherwise.
    """
    try:
      header_struct = self.HEADER.parseString(line)
    except pyparsing.ParseException:
      logging.debug(u'Not a Popularity Contest log file, invalid header')
      return False
    if not timelib.Timestamp.FromPosixTime(header_struct.epoch):
      logging.debug(u'Invalid Popularity Contest log file header timestamp.')
      return False
    return True

  def ParseRecord(self, parser_mediator, key, structure):
    """Parse each record structure and return an EventObject if applicable.

    Args:
      parser_mediator: A parser mediator object (instance of ParserMediator).
      key: An identification string indicating the name of the parsed
           structure.
      structure: A pyparsing.ParseResults object from a line in the
                 log file.

    Returns:
      An event object (instance of EventObject) or None.
    """
    # TODO: Add anomaly objects for abnormal timestamps, such as when the log
    # timestamp is greater than the session start.
    if key == 'logline':
      return self._ParseLogLine(structure)
    elif key == 'header':
      if not structure.epoch:
        logging.debug(u'PopularityContestParser, header with invalid epoch.')
        return
      return PopularityContestSessionEvent(
          structure.epoch, unicode(structure.session), u'start', structure.id,
          structure.details)
    elif key == 'footer':
      if not structure.epoch:
        logging.debug(u'PopularityContestParser, footer with invalid epoch.')
        return
      return PopularityContestSessionEvent(
          structure.epoch, unicode(structure.session), u'end')
    else:
      logging.warning(
          u'PopularityContestParser, unknown structure: {}.'.format(key))

  def _ParseLogLine(self, structure):
    """Gets an event_object or None from the pyparsing ParseResults.

    Args:
      structure: the pyparsing ParseResults object.

    Returns:
      event_object: a plaso event or None.
    """
    # Required fields are <mru> and <atime> and we are not interested in
    # log lines without <mru>.
    if not structure.mru:
      return
    # The <atime> field (as <ctime>) is always present but could be 0.
    # In case of <atime> equal to 0, we are in <NOFILES> case, safely return
    # without logging.
    if not structure.atime:
      return
    # TODO: not doing any check on <tag> fields, even if only informative
    # probably it could be better to check for the expected values.
    # TODO: ctime is a numeric string representing seconds since epoch UTC,
    # reconsider a conversion to integer together with microseconds usage.
    return PopularityContestEvent(
        structure.atime, structure.ctime, structure.package, structure.mru,
        structure.tag)


manager.ParsersManager.RegisterParser(PopularityContestParser)
