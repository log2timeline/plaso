#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 The Plaso Project Authors.
# Please see the AUTHORS file for details on individual authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""This file contains the worker class for Plaso.

The worker in Plaso monitors a queue filled with PathSpec protobufs,
which describe files that need to be processed. The worker then opens
up the file, as described in the protobuf, and sends it to a classifier
that determines the file type. Based on the file type from the classifier
the worker then sends the file to the appropriate parsers that take care
of extracting EventObjects from it.
"""
import copy
import gzip
import logging
import os
import pdb
import tarfile
import zipfile
import zlib

from plaso import parsers   # pylint: disable-msg=W0611
from plaso.lib import errors
from plaso.lib import event
from plaso.lib import pfilter
from plaso.lib import putils
from plaso.lib import utils
from plaso.pvfs import pfile
from plaso.pvfs import pvfs


class PlasoWorker(object):
  """A class that retrieves file information from a queue and parses them.

  This class is designed to watch a queue filled with protobufs describing
  the layout and paths to a file that needs to be further processed. The class
  uses that description to create a PFile object, which is a file like object
  and sends it to a classifier, followed by calls to the appropriate parsers.

  The class therefore needs to determine if that particular file can be parsed
  by the tool or not. If the tool is capable of parsing said file then it sends
  all extracted EventObjects from it into the storage queue for further
  processing.
  """

  # TODO: Change this when the classifier is ready and use that
  # instead to determine if a file is compressed or not.
  # So this is TEMPORARY until the classifier is ready and can be used.
  # Otherwise we check all files for this support and it can sometimes
  # be VERY slow, since some of the underlying libraries use unbound
  # read operation, reading in entire files, that may be very large.
  MAGIC_VALUES = {
      'ZIP': {'length': 4, 'offset': 0, 'values': ['P', 'K', '\x03', '\x04']},
      'TAR': {'length': 5, 'offset': 257, 'values': ['u', 's', 't', 'a', 'r']},
      'GZ': {'length': 2, 'offset': 0, 'values': ['\x1f', '\x8b']},
  }

  # TODO: Remove this logic when the classifier is ready.
  # This is only used temporary until files can be classified.
  magic_max_length = 0

  # Defines the maximum depth into a file (for SmartOpenFiles).
  MAX_FILE_DEPTH = 3

  def __init__(self, identifier, proc_queue, stor_queue, config, pre_obj):
    """Constructor for the class.

    Args:
      identifier: A thread identifier, usually an incrementing integer.
      proc_queue: A queue containing the filehandles needed to be processed.
      stor_queue: A queue that extracted EventObjects should be added to.
      config: A config object that contains all the tool's configuration.
      pre_obj: A PlasoPreprocess object containing information collected from
      image.
    """
    self._identifier = identifier
    self._proc_queue = proc_queue
    self._stor_queue = stor_queue
    self.config = config
    self._pre_obj = pre_obj
    self._parsers = putils.FindAllParsers(
        pre_obj, config, getattr(config, 'parsers', ''))
    self._user_mapping = self._GetUserMapping()

    if hasattr(config, 'image') and config.image:
      self._fscache = pvfs.FilesystemCache()

    self._filter = None
    filter_query = getattr(config, 'filter', None)
    if filter_query:
      self._filter = pfilter.GetMatcher(filter_query)

  def Run(self):
    """Start the worker, monitor the queue and parse files."""
    self.pid = os.getpid()
    logging.info(
        u'Worker %d (PID: %d) started monitoring process queue.',
        self._identifier, self.pid)

    for item in self._proc_queue.PopItems():
      # TODO: Remove this "ugly" hack in favor of something more elegant
      # and one that makes more sense.
      if item.startswith('P'):
        self.ParsePathSpec(item)
      elif item.startswith('B'):
        self.ParseBundle(item)
      else:
        logging.error(
            u'Unable to unserialize pathspec, wrong type: %s', item[0])

    logging.info(
        'Worker %d (PID: %d) stopped monitoring process queue.',
        self._identifier, os.getpid())

  def ParseBundle(self, bundle_string):
    """Parse a file given a serialized pathspec bundle."""
    bundle = event.EventPathBundle()
    try:
      bundle.FromProtoString(bundle_string)
    except RuntimeError:
      logging.debug(
          (u'Error while trying to parse a PathSpecBundle from the queue. '
           'The bundle that caused the error:\n%s'), bundle_string)
      return

    print bundle.ToProto()
    # GO OVER ALL BUNDLE PARSERS!
    #          self._ParseEvent(evt, filehandle, parsing_object.parser_name,
    #                           stat_obj)

  def ParsePathSpec(self, pathspec_string):
    """Parse a file given a serialized pathspec."""
    pathspec = event.EventPathSpec()
    if hasattr(self.config, 'text_prepend'):
      pathspec.path_prepend = self.config.text_prepend

    try:
      pathspec.FromProtoString(pathspec_string)
    except RuntimeError:
      logging.debug(
          (u'Error while trying to parse a PathSpec from the queue.'
           'The PathSpec that caused the error:\n%s'), pathspec_string)
      return

    # Either parse this file and all extracted files, or just the file.
    try:
      with pfile.OpenPFile(
          pathspec, fscache=getattr(self, '_fscache', None)) as fh:
        self.ParseFile(fh)
        if self.config.open_files:
          self.ParseAllFiles(fh)
    except IOError as e:
      logging.warning(u'Unable to parse file: %s (%s)', pathspec.file_path, e)
      logging.warning(
          u'Proto\n%s\n%s\n%s', '-+' * 20, pathspec.ToProto(), '-+' * 20)

  def ParseAllFiles(self, filehandle):
    """Parse every file that can be extracted from a PFile object.

    Args:
      filehandle: A PFile object.
    """
    try:
      for fh in self.SmartOpenFiles(
          filehandle, getattr(self, '_fscache', None)):
        self.ParseFile(fh)
    except IOError as e:
      logging.debug(('Unable to open file: {%s}, not sure if we can extract '
                     'further files from it. Msg: %s'),
                    filehandle.display_name, e)

  def _GetUserMapping(self):
    """Return a user dict which maps SID/UID values and usernames."""
    user_dict = {}

    if not getattr(self, '_pre_obj', None):
      return user_dict

    for user in getattr(self._pre_obj, 'users', []):
      sid = user.get('sid', '')
      if sid:
        value = sid
      else:
        value = user.get('uid', '')

      if value:
        user_dict[value] = user.get('name', value)

    return user_dict

  def _ParseEvent(self, event_object, filehandle, parser_name, stat_obj):
    """Adjust value of an extracted EventObject before storing it."""
    # TODO: Make some more adjustments to the event object.
    # Need to apply time skew, and other information extracted from
    # the configuration of the tool.
    if not hasattr(event_object, 'offset'):
      event_object.offset = filehandle.tell()
    event_object.display_name = filehandle.display_name
    event_object.filename = filehandle.name
    event_object.pathspec = filehandle.pathspec_root
    event_object.parser = parser_name
    if hasattr(self._pre_obj, 'hostname'):
      event_object.hostname = self._pre_obj.hostname
    if not hasattr(event_object, 'inode') and hasattr(stat_obj, 'ino'):
      event_object.inode = utils.GetInodeValue(stat_obj.ino)

    # Set the username that is associated to the record.
    if getattr(event_object, 'user_sid', None) and self._user_mapping:
      username = self._user_mapping.get(event_object.user_sid, None)
      if username:
        event_object.username = username

    if not self._filter:
      self._stor_queue.AddEvent(event_object.ToProtoString())
    else:
      if self._filter.Matches(event_object):
        self._stor_queue.AddEvent(event_object.ToProtoString())

  def ParseFile(self, filehandle):
    """Run through classifier and appropriate parsers.

    Args:
      filehandle: A file like object that should be checked.
    """
    logging.debug('[ParseFile] Parsing: %s', filehandle.display_name)

    # TODO: Not go through all parsers, just the ones
    # that the classifier classifies the file as.
    # Do this when classifier is ready (cl/30332229).
    # The classifier will return a "type" back, which refers
    # to a key in the self._parsers dict. If the results are
    # inconclusive the "all" key is used, or the key is not found.
    # key = self._parsers.get(classification, 'all')
    stat_obj = filehandle.Stat()
    for parsing_object in self._parsers['all']:
      logging.debug('Checking [%s] against: %s', filehandle.name,
                    parsing_object.parser_name)
      try:
        filehandle.seek(0)
        for evt in parsing_object.Parse(filehandle):
          if evt:
            if isinstance(evt, event.EventObject):
              self._ParseEvent(
                  evt, filehandle, parsing_object.parser_name, stat_obj)
            elif isinstance(evt, event.EventContainer):
              for event_object in evt:
                self._ParseEvent(
                    event_object, filehandle, parsing_object.parser_name,
                    stat_obj)

      except errors.UnableToParseFile as e:
        logging.debug('Not a %s file (%s) - %s', parsing_object.parser_name,
                      filehandle.name, e)
      except IOError as e:
        logging.debug('Unable to parse: %s [%s] using %s', filehandle.name,
                      filehandle.display_name, parsing_object.parser_name)
      # Casting a wide net, catching all exceptions. Done to keep the worker
      # running, despite the parser hitting errors, so the worker doesn't die
      # if a single file is corrupted or there is a bug in a parser.
      except Exception as e:
        logging.warning(('An unexpected error occured during processing of '
                         'file: %s using module %s. The error was: %s.\nParsin'
                         'g of file is is terminated.'), filehandle.name,
                        parsing_object.parser_name, e)
        logging.debug('The PathSpec that caused the error:\n(root)\n%s\n%s',
                      filehandle.pathspec_root.ToProto(),
                      filehandle.pathspec.ToProto())
        logging.exception(e)

        # Check for debug mode and single-threaded, then we would like
        # to debug this problem.
        if self.config.single_thread and self.config.debug:
          pdb.post_mortem()

    logging.debug('[ParseFile] Parsing DONE: %s', filehandle.display_name)

  @classmethod
  def SmartOpenFiles(cls, fh, fscache=None, depth=0):
    """Generate a list of all available PathSpecs extracted from a file.

    Args:
      fh: A PFile object that is used to extract PathSpecs from.
      fscache: A pfile.FilesystemCache object.
      depth: Incrementing number that defines the current depth into
             a file (file inside a ZIP file is depth 1, file inside a tar.gz
             would be of depth 2).

    Yields:
      A Pfile file-like object.
    """
    if depth >= cls.MAX_FILE_DEPTH:
      return

    for pathspec in cls.SmartOpenFile(fh):
      try:
        pathspec_orig = copy.deepcopy(pathspec)
        new_fh = pfile.OpenPFile(
            spec=pathspec, orig=pathspec_orig, fscache=fscache)
        yield new_fh
      except IOError as e:
        logging.debug(('Unable to open file: {%s}, not sure if we can extract '
                       'further files from it. Msg: %s'), fh.display_name, e)
        continue
      for new_filehandle in cls.SmartOpenFiles(new_fh, fscache, depth + 1):
        yield new_filehandle

  @classmethod
  def SmartOpenFile(cls, fh):
    """Return a generator for all pathspec protobufs extracted from a PFile.

    If the file is compressed then extract all members and include
    them into the processing queue.

    Args:
      fh: The filehandle we are examining.

    Yields:
      EventPathSpec objects describing how a file can be opened.
    """
    # TODO: Remove when classifier gets deployed. Then we
    # call the classifier here and use that for definition (and
    # then we forward the classifier definition in the pathspec
    # protobuf.
    fh.seek(0)

    if not cls.magic_max_length:
      for magic_value in cls.MAGIC_VALUES.values():
        cls.magic_max_length = max(
            cls.magic_max_length,
            magic_value['length'] + magic_value['offset'])

    header = fh.read(cls.magic_max_length)

    file_classification = ''
    # Go over each and every magic value defined and compare
    # each read byte (according to original offset and current one)
    # If all match, then we have a particular file format and we
    # can move on.
    for m_value, m_dict in cls.MAGIC_VALUES.items():
      length = m_dict['length'] + m_dict['offset']
      if len(header) < length:
        continue

      offset = m_dict['offset']
      magic = m_dict['values']

      if header[offset:offset + len(magic)] == ''.join(magic):
        file_classification = m_value
        break

    if file_classification == 'ZIP':
      try:
        fh.seek(0)
        fh_zip = zipfile.ZipFile(fh, 'r')

        # TODO: Make this is a more "sane" check, and perhaps
        # not entirely skip the file if it has this particular
        # ending, but for now, this both slows the tool down
        # considerably and makes it also more unstable.
        file_ending = fh.name.lower()[-4:]
        if file_ending in ['.jar', '.sym', '.xpi']:
          logging.debug(
              u'ZIP but the wrong type of zip [%s]: %s', file_ending, fh.name)
          return

        container_path = fh.pathspec.file_path
        root_pathspec = fh.pathspec_root
        for info in fh_zip.infolist():
          if info.file_size > 0:
            logging.debug(u'Including: %s from ZIP into process queue.',
                          info.filename)
            pathspec = copy.deepcopy(root_pathspec)
            transfer_zip = event.EventPathSpec()
            transfer_zip.type = 'ZIP'
            transfer_zip.file_path = utils.GetUnicodeString(info.filename)
            transfer_zip.container_path = utils.GetUnicodeString(
                container_path)
            cls.SetNestedContainer(pathspec, transfer_zip)
            yield pathspec
        return
      except zipfile.BadZipfile:
        pass

    if file_classification == 'GZ':
      try:
        fh.seek(0)
        if fh.pathspec.type == 'GZIP':
          raise errors.SameFileType
        fh_gzip = gzip.GzipFile(fileobj=fh, mode='rb')
        _ = fh_gzip.read(4)
        fh_gzip.seek(0)
        logging.debug(u'Including: %s from GZIP into process queue.', fh.name)
        transfer_gzip = event.EventPathSpec()
        transfer_gzip.type = 'GZIP'
        transfer_gzip.file_path = utils.GetUnicodeString(fh.pathspec.file_path)
        pathspec = copy.deepcopy(fh.pathspec_root)
        cls.SetNestedContainer(pathspec, transfer_gzip)
        yield pathspec
        return
      except (IOError, zlib.error, errors.SameFileType):
        pass

    # TODO: Add BZ2 support, in most cases it should be the same
    # as gzip support, however the library does not accept filehandles,
    # it requires a filename/path.

    if file_classification == 'TAR':
      try:
        fh.seek(0)
        fh_tar = tarfile.open(fileobj=fh, mode='r')
        root_pathspec = fh.pathspec_root
        file_path = fh.pathspec.file_path
        for name_info in fh_tar.getmembers():
          if not name_info.isfile():
            continue
          name = name_info.path
          logging.debug(u'Including: %s from TAR into process queue.', name)
          pathspec = copy.deepcopy(root_pathspec)
          transfer_tar = event.EventPathSpec()
          transfer_tar.type = 'TAR'
          transfer_tar.file_path = utils.GetUnicodeString(name)
          transfer_tar.container_path = utils.GetUnicodeString(file_path)
          cls.SetNestedContainer(pathspec, transfer_tar)
          yield pathspec
        return
      except tarfile.ReadError:
        pass

  @classmethod
  def SetNestedContainer(cls, pathspec_root, pathspec_append):
    """Append an EventPathSpec to the end of a nested_pathspec chain.

    Args:
      pathspec_root: The root EventPathSpec of the chain.
      pathspec_append: The EventPathSpec that needs to be appended.
    """
    if not hasattr(pathspec_root, 'nested_pathspec'):
      pathspec_root.nested_pathspec = pathspec_append
    else:
      cls.SetNestedContainer(pathspec_root.nested_pathspec, pathspec_append)


# TODO: Add a main function that can be used to execute the
# worker directly, so it can be run independently.

