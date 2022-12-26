# -*- coding: utf-8 -*-
"""Text parser plugin for popularity contest log files.

Information updated 20 january 2014.
From Debian Package Popularity Contest
Avery Pennarun <apenwarr@debian.org>

From 'https://www.unix.com/man-page/Linux/8/popularity-contest':

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
    https://popcon.debian.org

    Normally,    popularity-contest    is   run   from   a cron(8)   job,
    /etc/cron.daily/popularity-contest,  which  automatically  submits  the
    results  to  Debian package maintainers (only once a week) according to
    the settings in /etc/popularity-contest.conf and /usr/share/popularity-
    contest/default.conf.


From 'https://popcon.ubuntu.com/README':

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

import pyparsing

from dfdatetime import posix_time as dfdatetime_posix_time

from plaso.containers import events
from plaso.lib import errors
from plaso.parsers import text_parser
from plaso.parsers.text_plugins import interface


class PopularityContestSessionEventData(events.EventData):
  """Popularity Contest session event data.

  Attributes:
    details (str): version and host architecture.
    end_time (dfdatetime.DateTimeValues): date and time the end of the session
        log entry was added.
    host_identifier (str): host identifier (UUID).
    session (int): session number.
    start_time (dfdatetime.DateTimeValues): date and time the start of
        the session log entry was added.
  """

  DATA_TYPE = 'linux:popularity_contest_log:session'

  def __init__(self):
    """Initializes event data."""
    super(PopularityContestSessionEventData, self).__init__(
        data_type=self.DATA_TYPE)
    self.details = None
    self.end_time = None
    self.host_identifier = None
    self.session = None
    self.start_time = None


class PopularityContestEventData(events.EventData):
  """Popularity Contest event data.

  Attributes:
    access_time (dfdatetime.DateTimeValues): file entry last access date
        and time.
    change_time (dfdatetime.DateTimeValues): file entry inode change
        (or metadata last modification) date and time.
    mru (str): recently used app/library from package.
    package (str): installed packaged name, which the mru belongs to.
    record_tag (str): popularity context tag.
  """

  DATA_TYPE = 'linux:popularity_contest_log:entry'

  def __init__(self):
    """Initializes event data."""
    super(PopularityContestEventData, self).__init__(data_type=self.DATA_TYPE)
    self.access_time = None
    self.change_time = None
    self.mru = None
    self.package = None
    self.record_tag = None


class PopularityContestTextPlugin(interface.TextPlugin):
  """Text parser plugin for popularity contest log files."""

  NAME = 'popularity_contest'
  DATA_FORMAT = 'Popularity Contest log file'

  ENCODING = 'utf-8'

  _INTEGER = pyparsing.Word(pyparsing.nums).setParseAction(
      lambda tokens: int(tokens[0], 10))

  _UNICODE_PRINTABLES = ''.join(
      chr(character) for character in range(65536)
      if not chr(character).isspace())

  _MRU = pyparsing.Word(_UNICODE_PRINTABLES).setResultsName('mru')
  _TAG = pyparsing.QuotedString('<', endQuoteChar='>').setResultsName('tag')

  _END_OF_LINE = pyparsing.Suppress(pyparsing.LineEnd())

  _HEADER_LINE = (
      pyparsing.Suppress('POPULARITY-CONTEST-') +
      _INTEGER.setResultsName('session') +
      pyparsing.Suppress('TIME:') + _INTEGER.setResultsName('timestamp') +
      pyparsing.Suppress('ID:') +
      pyparsing.Word(pyparsing.alphanums, exact=32).setResultsName('id') +
      pyparsing.restOfLine().setResultsName('details') +
      _END_OF_LINE)

  _FOOTER_LINE = (
      pyparsing.Suppress('END-POPULARITY-CONTEST-') +
      _INTEGER.setResultsName('session') +
      pyparsing.Suppress('TIME:') + _INTEGER.setResultsName('timestamp') +
      _END_OF_LINE)

  _LOG_LINE = (
      _INTEGER.setResultsName('atime') +
      _INTEGER.setResultsName('ctime') +
      pyparsing.Word(pyparsing.printables).setResultsName('package') +
      (_TAG ^ (_MRU + _TAG) ^ _MRU) +
      _END_OF_LINE)

  _LINE_STRUCTURES = [
      ('footer_line', _FOOTER_LINE),
      ('header_line', _HEADER_LINE),
      ('log_line', _LOG_LINE)]

  VERIFICATION_GRAMMAR = _HEADER_LINE

  def __init__(self):
    """Initializes a text parser plugin."""
    super(PopularityContestTextPlugin, self).__init__()
    self._session_event_data = None

  def _GetDateTimeValueFromStructure(self, structure, name):
    """Retrieves a date and time value from a Pyparsing structure.

    Args:
      structure (pyparsing.ParseResults): tokens from a parsed log line.
      name (str): name of the token.

    Returns:
      dfdatetime.TimeElements: date and time value or None if not available.
    """
    timestamp = self._GetValueFromStructure(structure, name)
    if not timestamp:
      return None

    return dfdatetime_posix_time.PosixTime(timestamp=timestamp)

  def _ParseLogLine(self, parser_mediator, structure):
    """Extracts events from a log line.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      structure (pyparsing.ParseResults): structure parsed from the log file.
    """
    # The <atime> field (as <ctime>) is always present but could be 0.
    # In case of <atime> equal to 0, we are in <NOFILES> case, safely return
    # without logging.

    # TODO: not doing any check on <tag> fields, even if only informative
    # probably it could be better to check for the expected values.

    # Required fields are <mru> and <atime> and we are not interested in
    # log lines without <mru>.
    if 'mru' not in structure:
      return

    event_data = PopularityContestEventData()

    event_data.access_time = self._GetDateTimeValueFromStructure(
        structure, 'atime')

    event_data.change_time = self._GetDateTimeValueFromStructure(
        structure, 'ctime')

    event_data.mru = self._GetValueFromStructure(structure, 'mru')
    event_data.package = self._GetValueFromStructure(structure, 'package')
    event_data.record_tag = self._GetValueFromStructure(structure, 'tag')

    parser_mediator.ProduceEventData(event_data)

  def _ParseRecord(self, parser_mediator, key, structure):
    """Parses a pyparsing structure.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      key (str): name of the parsed structure.
      structure (pyparsing.ParseResults): tokens from a parsed log line.

    Raises:
      ParseError: if the structure cannot be parsed.
    """
    if key == 'log_line':
      self._ParseLogLine(parser_mediator, structure)

    elif key in ('footer_line', 'header_line'):
      date_time = self._GetDateTimeValueFromStructure(
          structure, 'timestamp')

      session = self._GetValueFromStructure(structure, 'session')

      if key == 'header_line':
        self._session_event_data = PopularityContestSessionEventData()
        self._session_event_data.session = session
        self._session_event_data.start_time = date_time

        self._session_event_data.details = self._GetStringValueFromStructure(
            structure, 'details')
        self._session_event_data.host_identifier = self._GetValueFromStructure(
            structure, 'id')

      elif key == 'footer_line':
        # TODO: check session

        self._session_event_data.end_time = date_time

        parser_mediator.ProduceEventData(self._session_event_data)

        self._session_event_data = None

  def CheckRequiredFormat(self, parser_mediator, text_reader):
    """Check if the log record has the minimal structure required by the plugin.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      text_reader (EncodedTextReader): text reader.

    Returns:
      bool: True if this is the correct parser, False otherwise.
    """
    try:
      self._VerifyString(text_reader.lines)
    except errors.ParseError:
      return False

    self._session_event_data = None

    return True


text_parser.TextLogParser.RegisterPlugin(PopularityContestTextPlugin)
