# -*- coding: utf-8 -*-
"""SQLite parser plugin for Kodi videos database files."""

from dfdatetime import time_elements as dfdatetime_time_elements

from plaso.containers import events
from plaso.parsers import sqlite
from plaso.parsers.sqlite_plugins import interface


class KodiVideoEventData(events.EventData):
  """Kodi video event data.

  Attributes:
    filename (str): video filename.
    last_played_time (dfdatetime.DateTimeValues): date and time of the last
        occurrence the video was played.
    play_count (int): number of times the video has been played.
    query (str): SQL query that was used to obtain the event data.
  """

  DATA_TYPE = 'kodi:videos:viewing'

  def __init__(self):
    """Initializes event data."""
    super(KodiVideoEventData, self).__init__(data_type=self.DATA_TYPE)
    self.filename = None
    self.last_played_time = None
    self.play_count = None
    self.query = None


class KodiMyVideosPlugin(interface.SQLitePlugin):
  """SQLite parser plugin for Kodi videos database files.

  The Kodi videos database file is typically stored in:
  MyVideos.db
  """

  NAME = 'kodi'
  DATA_FORMAT = 'Kodi videos SQLite database (MyVideos.db) file'

  REQUIRED_STRUCTURE = {
      'files': frozenset([
          'idFile', 'strFilename', 'playCount', 'lastPlayed'])}

  QUERIES = [
      ('SELECT idFile, strFilename, playCount, lastPlayed FROM files',
       'ParseVideoRow')]

  SCHEMAS = [{
      'actor': (
          'CREATE TABLE actor ( actor_id INTEGER PRIMARY KEY, name TEXT, '
          'art_urls TEXT )'),
      'actor_link': (
          'CREATE TABLE actor_link(actor_id INTEGER, media_id INTEGER, '
          'media_type TEXT, role TEXT, cast_order INTEGER)'),
      'art': (
          'CREATE TABLE art(art_id INTEGER PRIMARY KEY, media_id INTEGER, '
          'media_type TEXT, type TEXT, url TEXT)'),
      'bookmark': (
          'CREATE TABLE bookmark ( idBookmark integer primary key, idFile '
          'integer, timeInSeconds double, totalTimeInSeconds double, '
          'thumbNailImage text, player text, playerState text, type integer)'),
      'country': (
          'CREATE TABLE country ( country_id integer primary key, name TEXT)'),
      'country_link': (
          'CREATE TABLE country_link (country_id integer, media_id integer, '
          'media_type TEXT)'),
      'director_link': (
          'CREATE TABLE director_link(actor_id INTEGER, media_id INTEGER, '
          'media_type TEXT)'),
      'episode': (
          'CREATE TABLE episode ( idEpisode integer primary key, idFile '
          'integer,c00 text,c01 text,c02 text,c03 text,c04 text,c05 text,c06 '
          'text,c07 text,c08 text,c09 text,c10 text,c11 text,c12 '
          'varchar(24),c13 varchar(24),c14 text,c15 text,c16 text,c17 '
          'varchar(24),c18 text,c19 text,c20 text,c21 text,c22 text,c23 text, '
          'idShow integer, userrating integer, idSeason integer)'),
      'files': (
          'CREATE TABLE files ( idFile integer primary key, idPath integer, '
          'strFilename text, playCount integer, lastPlayed text, dateAdded '
          'text)'),
      'genre': (
          'CREATE TABLE genre ( genre_id integer primary key, name TEXT)'),
      'genre_link': (
          'CREATE TABLE genre_link (genre_id integer, media_id integer, '
          'media_type TEXT)'),
      'movie': (
          'CREATE TABLE movie ( idMovie integer primary key, idFile '
          'integer,c00 text,c01 text,c02 text,c03 text,c04 text,c05 text,c06 '
          'text,c07 text,c08 text,c09 text,c10 text,c11 text,c12 text,c13 '
          'text,c14 text,c15 text,c16 text,c17 text,c18 text,c19 text,c20 '
          'text,c21 text,c22 text,c23 text, idSet integer, userrating '
          'integer, premiered text)'),
      'movielinktvshow': (
          'CREATE TABLE movielinktvshow ( idMovie integer, IdShow integer)'),
      'musicvideo': (
          'CREATE TABLE musicvideo ( idMVideo integer primary key, idFile '
          'integer,c00 text,c01 text,c02 text,c03 text,c04 text,c05 text,c06 '
          'text,c07 text,c08 text,c09 text,c10 text,c11 text,c12 text,c13 '
          'text,c14 text,c15 text,c16 text,c17 text,c18 text,c19 text,c20 '
          'text,c21 text,c22 text,c23 text, userrating integer, premiered '
          'text)'),
      'path': (
          'CREATE TABLE path ( idPath integer primary key, strPath text, '
          'strContent text, strScraper text, strHash text, scanRecursive '
          'integer, useFolderNames bool, strSettings text, noUpdate bool, '
          'exclude bool, dateAdded text, idParentPath integer)'),
      'rating': (
          'CREATE TABLE rating (rating_id INTEGER PRIMARY KEY, media_id '
          'INTEGER, media_type TEXT, rating_type TEXT, rating FLOAT, votes '
          'INTEGER)'),
      'seasons': (
          'CREATE TABLE seasons ( idSeason integer primary key, idShow '
          'integer, season integer, name text, userrating integer)'),
      'sets': (
          'CREATE TABLE sets ( idSet integer primary key, strSet text, '
          'strOverview text)'),
      'settings': (
          'CREATE TABLE settings ( idFile integer, Deinterlace bool,ViewMode '
          'integer,ZoomAmount float, PixelRatio float, VerticalShift float, '
          'AudioStream integer, SubtitleStream integer,SubtitleDelay float, '
          'SubtitlesOn bool, Brightness float, Contrast float, Gamma '
          'float,VolumeAmplification float, AudioDelay float, '
          'OutputToAllSpeakers bool, ResumeTime integer,Sharpness float, '
          'NoiseReduction float, NonLinStretch bool, PostProcess '
          'bool,ScalingMethod integer, DeinterlaceMode integer, StereoMode '
          'integer, StereoInvert bool, VideoStream integer)'),
      'stacktimes': (
          'CREATE TABLE stacktimes (idFile integer, times text)'),
      'streamdetails': (
          'CREATE TABLE streamdetails (idFile integer, iStreamType integer, '
          'strVideoCodec text, fVideoAspect float, iVideoWidth integer, '
          'iVideoHeight integer, strAudioCodec text, iAudioChannels integer, '
          'strAudioLanguage text, strSubtitleLanguage text, iVideoDuration '
          'integer, strStereoMode text, strVideoLanguage text)'),
      'studio': (
          'CREATE TABLE studio ( studio_id integer primary key, name TEXT)'),
      'studio_link': (
          'CREATE TABLE studio_link (studio_id integer, media_id integer, '
          'media_type TEXT)'),
      'tag': (
          'CREATE TABLE tag (tag_id integer primary key, name TEXT)'),
      'tag_link': (
          'CREATE TABLE tag_link (tag_id integer, media_id integer, '
          'media_type TEXT)'),
      'tvshow': (
          'CREATE TABLE tvshow ( idShow integer primary key,c00 text,c01 '
          'text,c02 text,c03 text,c04 text,c05 text,c06 text,c07 text,c08 '
          'text,c09 text,c10 text,c11 text,c12 text,c13 text,c14 text,c15 '
          'text,c16 text,c17 text,c18 text,c19 text,c20 text,c21 text,c22 '
          'text,c23 text, userrating integer, duration INTEGER)'),
      'tvshowlinkpath': (
          'CREATE TABLE tvshowlinkpath (idShow integer, idPath integer)'),
      'uniqueid': (
          'CREATE TABLE uniqueid (uniqueid_id INTEGER PRIMARY KEY, media_id '
          'INTEGER, media_type TEXT, value TEXT, type TEXT)'),
      'version': (
          'CREATE TABLE version (idVersion integer, iCompressCount integer)'),
      'writer_link': (
          'CREATE TABLE writer_link(actor_id INTEGER, media_id INTEGER, '
          'media_type TEXT)')}]

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
    time_string = self._GetRowValue(query_hash, row, value_name)
    if time_string is None:
      return None

    date_time = dfdatetime_time_elements.TimeElements()
    date_time.CopyFromDateTimeString(time_string)
    return date_time

  def ParseVideoRow(self, parser_mediator, query, row, **unused_kwargs):
    """Parses a Video row.

    Args:
      parser_mediator (ParserMediator): mediates interactions between parsers
          and other components, such as storage and dfVFS.
      query (str): query that created the row.
      row (sqlite3.Row): row.
    """
    query_hash = hash(query)

    event_data = KodiVideoEventData()
    event_data.filename = self._GetRowValue(query_hash, row, 'strFilename')
    event_data.last_played_time = self._GetDateTimeRowValue(
        query_hash, row, 'lastPlayed')
    event_data.play_count = self._GetRowValue(query_hash, row, 'playCount')
    event_data.query = query

    parser_mediator.ProduceEventData(event_data)


sqlite.SQLiteParser.RegisterPlugin(KodiMyVideosPlugin)
