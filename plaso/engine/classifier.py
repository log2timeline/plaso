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

import gzip
import logging
import os
import tarfile
import zipfile
import zlib

from dfvfs.lib import definitions
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.lib import errors


class Classifier(object):
  """Class that defines the file format classifier."""

  _MAGIC_VALUES = {
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
  def _SmartOpenFile(cls, file_entry):
    """Return a generator for all pathspec protobufs extracted from a file.

    If the file is compressed then extract all members and include
    them into the processing queue.

    Args:
      file_entry: The file entry object.

    Yields:
      A path specification (instance of dfvfs.PathSpec) of embedded file
      entries.
    """
    file_object = file_entry.GetFileObject()

    # TODO: Remove when classifier gets deployed. Then we
    # call the classifier here and use that for definition (and
    # then we forward the classifier definition in the pathspec
    # protobuf.
    file_object.seek(0, os.SEEK_SET)

    if not cls.magic_max_length:
      for magic_value in cls._MAGIC_VALUES.values():
        cls.magic_max_length = max(
            cls.magic_max_length,
            magic_value['length'] + magic_value['offset'])

    header = file_object.read(cls.magic_max_length)

    file_classification = ''
    # Go over each and every magic value defined and compare
    # each read byte (according to original offset and current one)
    # If all match, then we have a particular file format and we
    # can move on.
    for m_value, m_dict in cls._MAGIC_VALUES.items():
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
        _, _, filename_extension = file_entry.name.rpartition(u'.')

        if filename_extension in [u'.jar', u'.sym', u'.xpi']:
          file_object.close()
          logging.debug(
              u'Unsupported ZIP sub type: {0:s} detected in file: {1:s}'.format(
                  filename_extension, file_entry.path_spec.comparable))
          return

        for info in zip_file.infolist():
          if info.file_size > 0:
            logging.debug(
                u'Including: {0:s} from ZIP into process queue.'.format(
                    info.filename))

            yield path_spec_factory.Factory.NewPathSpec(
                definitions.TYPE_INDICATOR_ZIP, location=info.filename,
                parent=file_entry.path_spec)

      except zipfile.BadZipfile:
        pass

    elif file_classification == 'GZ':
      try:
        type_indicator = file_entry.path_spec.type_indicator
        if type_indicator == definitions.TYPE_INDICATOR_GZIP:
          raise errors.SameFileType

        file_object.seek(0, os.SEEK_SET)
        gzip_file = gzip.GzipFile(fileobj=file_object, mode='rb')
        _ = gzip_file.read(4)
        gzip_file.close()

        logging.debug((
            u'Including: {0:s} as GZIP compressed stream into process '
            u'queue.').format(file_entry.name))

        yield path_spec_factory.Factory.NewPathSpec(
            definitions.TYPE_INDICATOR_GZIP, parent=file_entry.path_spec)

      except (IOError, zlib.error, errors.SameFileType):
        pass

    # TODO: Add BZ2 support.
    elif file_classification == 'TAR':
      try:
        file_object.seek(0, os.SEEK_SET)
        tar_file = tarfile.open(fileobj=file_object, mode='r')

        for name_info in tar_file.getmembers():
          if not name_info.isfile():
            continue

          name = name_info.path
          logging.debug(
              u'Including: {0:s} from TAR into process queue.'.format(name))

          yield path_spec_factory.Factory.NewPathSpec(
              definitions.TYPE_INDICATOR_TAR, location=name,
              parent=file_entry.path_spec)

      except tarfile.ReadError:
        pass

    file_object.close()

  @classmethod
  def SmartOpenFiles(cls, file_entry, depth=0):
    """Generate a list of all available PathSpecs extracted from a file.

    Args:
      file_entry: A file entry object.
      depth: Incrementing number that defines the current depth into
             a file (file inside a ZIP file is depth 1, file inside a tar.gz
             would be of depth 2).

    Yields:
      A file entry object (instance of dfvfs.FileEntry).
    """
    if depth >= cls.MAX_FILE_DEPTH:
      return

    for path_spec in cls._SmartOpenFile(file_entry):
      sub_file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
      if sub_file_entry is None:
        logging.debug(
            u'Unable to open file: {0:s}'.format(path_spec.comparable))
        continue
      yield sub_file_entry

      depth += 1
      for sub_file_entry in cls.SmartOpenFiles(sub_file_entry, depth=depth):
        yield sub_file_entry
