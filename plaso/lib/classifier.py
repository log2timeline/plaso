#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2014 The Plaso Project Authors.
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
"""The file format classifier."""

# TODO: rewrite most of the classifier in C and integrate with the code in:
# plaso/classifier

import copy
import gzip
import logging
import os
import tarfile
import zipfile
import zlib

from plaso.lib import errors
from plaso.lib import event
from plaso.pvfs import pfile
from plaso.lib import utils


class Classifier(object):
  """Class that defines the file format classifier."""

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

  @classmethod
  def SmartOpenFiles(cls, file_entry, depth=0):
    """Generate a list of all available PathSpecs extracted from a file.

    Args:
      file_entry: A file entry object.
      depth: Incrementing number that defines the current depth into
             a file (file inside a ZIP file is depth 1, file inside a tar.gz
             would be of depth 2).

    Yields:
      A Pfile file-like object.
    """
    if depth >= cls.MAX_FILE_DEPTH:
      return

    for pathspec in cls.SmartOpenFile(file_entry):
      try:
        pathspec_orig = copy.deepcopy(pathspec)
        new_file_entry = pfile.PFileResolver.OpenFileEntry(
            pathspec, orig=pathspec_orig)
        yield new_file_entry
      except IOError as e:
        logging.debug((
            u'Unable to open file: {{{0:s}}}, not sure if we can extract '
            u'further files from it. Msg: {1:s}').format(
                file_entry.display_name, e))
        continue
      for new_file_entry in cls.SmartOpenFiles(
          new_file_entry, depth=(depth + 1)):
        yield new_file_entry

  @classmethod
  def SmartOpenFile(cls, file_entry):
    """Return a generator for all pathspec protobufs extracted from a PFile.

    If the file is compressed then extract all members and include
    them into the processing queue.

    Args:
      file_entry: The file entry object.

    Yields:
      EventPathSpec objects describing how a file can be opened.
    """
    file_object = file_entry.Open()

    # TODO: Remove when classifier gets deployed. Then we
    # call the classifier here and use that for definition (and
    # then we forward the classifier definition in the pathspec
    # protobuf.
    file_object.seek(0, os.SEEK_SET)

    if not cls.magic_max_length:
      for magic_value in cls.MAGIC_VALUES.values():
        cls.magic_max_length = max(
            cls.magic_max_length,
            magic_value['length'] + magic_value['offset'])

    header = file_object.read(cls.magic_max_length)

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

    # TODO: refactor the file type specific code into sub functions.
    if file_classification == 'ZIP':
      try:
        file_object.seek(0, os.SEEK_SET)
        zip_file = zipfile.ZipFile(file_object, 'r')

        # TODO: Make this is a more "sane" check, and perhaps
        # not entirely skip the file if it has this particular
        # ending, but for now, this both slows the tool down
        # considerably and makes it also more unstable.
        file_ending = file_entry.name.lower()[-4:]
        if file_ending in ['.jar', '.sym', '.xpi']:
          file_object.close()
          logging.debug(u'ZIP but the wrong type of zip [{0:s}]: {1:s}'.format(
              file_ending, file_entry.name))
          return

        container_path = file_entry.pathspec.file_path
        root_pathspec = file_entry.pathspec_root
        for info in zip_file.infolist():
          if info.file_size > 0:
            logging.debug(
                u'Including: {0:s} from ZIP into process queue.'.format(
                    info.filename))
            pathspec = copy.deepcopy(root_pathspec)
            transfer_zip = event.EventPathSpec()
            transfer_zip.type = 'ZIP'
            transfer_zip.file_path = utils.GetUnicodeString(info.filename)
            transfer_zip.container_path = utils.GetUnicodeString(
                container_path)
            pathspec.AddNestedContainer(transfer_zip)
            yield pathspec
      except zipfile.BadZipfile:
        pass

    elif file_classification == 'GZ':
      try:
        file_object.seek(0, os.SEEK_SET)
        if file_entry.pathspec.type == 'GZIP':
          raise errors.SameFileType
        gzip_file = gzip.GzipFile(fileobj=file_object, mode='rb')
        _ = gzip_file.read(4)
        gzip_file.seek(0, os.SEEK_SET)
        logging.debug(u'Including: {0:s} from GZIP into process queue.'.format(
            file_entry.name))
        transfer_gzip = event.EventPathSpec()
        transfer_gzip.type = 'GZIP'
        transfer_gzip.file_path = utils.GetUnicodeString(
            file_entry.pathspec.file_path)
        pathspec = copy.deepcopy(file_entry.pathspec_root)
        pathspec.AddNestedContainer(transfer_gzip)
        yield pathspec
      except (IOError, zlib.error, errors.SameFileType):
        pass

    # TODO: Add BZ2 support, in most cases it should be the same
    # as gzip support, however the library does not accept file-like objects,
    # it requires a filename/path.

    elif file_classification == 'TAR':
      try:
        file_object.seek(0, os.SEEK_SET)
        tar_file = tarfile.open(fileobj=file_object, mode='r')
        root_pathspec = file_entry.pathspec_root
        file_path = file_entry.pathspec.file_path
        for name_info in tar_file.getmembers():
          if not name_info.isfile():
            continue
          name = name_info.path
          logging.debug(
              u'Including: {0:s} from TAR into process queue.'.format(name))
          pathspec = copy.deepcopy(root_pathspec)
          transfer_tar = event.EventPathSpec()
          transfer_tar.type = 'TAR'
          transfer_tar.file_path = utils.GetUnicodeString(name)
          transfer_tar.container_path = utils.GetUnicodeString(file_path)
          pathspec.AddNestedContainer(transfer_tar)
          yield pathspec
      except tarfile.ReadError:
        pass

    file_object.close()
