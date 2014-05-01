#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2013 The Plaso Project Authors.
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
"""Generic collector that supports both file system and image files."""

import hashlib
import logging
import os
import re
import sre_constants

from dfvfs.lib import definitions as dfvfs_definitions
from dfvfs.lib import errors as dfvfs_errors
from dfvfs.path import factory as path_spec_factory
from dfvfs.resolver import resolver as path_spec_resolver

from plaso.lib import errors
from plaso.lib import event
from plaso.lib import queue
from plaso.lib import utils
from plaso.parsers import filestat
from plaso.winreg import path_expander as winreg_path_expander


# TODO: refactor.
def _SendContainerToStorage(file_entry, storage_queue_producer):
  """Read events from a event container and send them to storage.

  Args:
    file_entry: The file entry object (instance of dfvfs.FileEntry).
    storage_queue_producer: the storage queue producer (instance of
                            EventObjectQueueProducer).
  """
  stat_object = file_entry.GetStat()

  for event_object in filestat.StatEvents.GetEventsFromStat(stat_object):
    # TODO: dfVFS refactor: move display name to output since the path
    # specification contains the full information.
    event_object.display_name = u'{:s}:{:s}'.format(
        file_entry.path_spec.type_indicator, file_entry.name)

    event_object.filename = file_entry.name
    event_object.pathspec = file_entry.path_spec
    event_object.parser = u'FileStatParser'
    event_object.inode = utils.GetInodeValue(stat_object.ino)

    storage_queue_producer.ProduceEventObject(event_object)


class Collector(queue.PathSpecQueueProducer):
  """Class that implements a collector object."""

  def __init__(
      self, process_queue, storage_queue_producer, source_path,
      source_path_spec):
    """Initializes the collector object.

       The collector discovers all the files that need to be processed by
       the workers. Once a file is discovered it added to the process queue
       as a path specification (instance of dfvfs.PathSpec).

    Args:
      process_queue: The files processing queue (instance of Queue).
      storage_queue_producer: the storage queue producer (instance of
                              EventObjectQueueProducer).
      source_path: Path of the source file or directory.
      source_path_spec: The source path specification (instance of
                        dfvfs.PathSpec) as determined by the file system
                        scanner. The default is None.
    """
    super(Collector, self).__init__(process_queue)
    self._filter_file_path = None
    self._hashlist = None
    self._pre_obj = None
    self._process_vss = None
    self._storage_queue_producer = storage_queue_producer
    # TODO: remove the need to pass source_path
    self._source_path = os.path.abspath(source_path)
    self._source_path_spec = source_path_spec
    self._vss_stores = None
    self.collect_directory_metadata = True

  def __enter__(self):
    """Enters a with statement."""
    return self

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Exits a with statement."""
    return

  def _CalculateNTFSTimeHash(self, file_entry):
    """Return a hash value calculated from a NTFS file's metadata.

    Args:
      file_entry: The file entry (instance of TSKFileEntry).

    Returns:
      A hash value (string) that can be used to determine if a file's timestamp
    value has changed.
    """
    stat_object = file_entry.GetStat()
    ret_hash = hashlib.md5()

    ret_hash.update('atime:{0}.{1}'.format(
        getattr(stat_object, 'atime', 0),
        getattr(stat_object, 'atime_nano', 0)))

    ret_hash.update('crtime:{0}.{1}'.format(
        getattr(stat_object, 'crtime', 0),
        getattr(stat_object, 'crtime_nano', 0)))

    ret_hash.update('mtime:{0}.{1}'.format(
        getattr(stat_object, 'mtime', 0),
        getattr(stat_object, 'mtime_nano', 0)))

    ret_hash.update('ctime:{0}.{1}'.format(
        getattr(stat_object, 'ctime', 0),
        getattr(stat_object, 'ctime_nano', 0)))

    return ret_hash.hexdigest()

  def _ProcessDirectory(self, file_entry):
    """Processes a directory and extract its metadata if necessary."""
    # Need to do a breadth-first search otherwise we'll hit the Python
    # maximum recursion depth.
    sub_directories = []

    for sub_file_entry in file_entry.sub_file_entries:
      try:
        if not sub_file_entry.IsAllocated() or sub_file_entry.IsLink():
          continue
      except dfvfs_errors.BackEndError as exception:
        logging.warning(
            u'Unable to process file: {0:s} with error: {1:s}'.format(
                sub_file_entry.path_spec.comparable.replace(
                    u'\n', u';'), exception))
        continue

      # For TSK-based file entries only, ignore the virtual /$OrphanFiles
      # directory.
      if sub_file_entry.type_indicator == dfvfs_definitions.TYPE_INDICATOR_TSK:
        if file_entry.IsRoot() and sub_file_entry.name == u'$OrphanFiles':
          continue

      if sub_file_entry.IsDirectory():
        if self.collect_directory_metadata:
          # TODO: solve this differently by putting the path specification
          # on the queue and have the filestat parser just extract the metadata.
          # self.ProducePathSpec(sub_file_entry.path_spec)
          _SendContainerToStorage(file_entry, self._storage_queue_producer)

        sub_directories.append(sub_file_entry)

      elif sub_file_entry.IsFile():
        # If we are dealing with a VSS we want to calculate a hash
        # value based on available timestamps and compare that to previously
        # calculated hash values, and only include the file into the queue if
        # the hash does not match.
        if self._process_vss:
          hash_value = self._CalculateNTFSTimeHash(sub_file_entry)

          inode = getattr(sub_file_entry.path_spec, 'inode', 0)
          if inode in self._hashlist:
            if hash_value in self._hashlist[inode]:
              continue

          self._hashlist.setdefault(inode, []).append(hash_value)

        self.ProducePathSpec(sub_file_entry.path_spec)

    for sub_file_entry in sub_directories:
      try:
        self._ProcessDirectory(sub_file_entry)
      except (dfvfs_errors.AccessError, dfvfs_errors.BackEndError) as exception:
        logging.warning(u'{0:s}'.format(exception))

  def _ProcessFileSystemWithFilter(self):
    """Processes the source path based on the collection filter."""
    preprocessor_collector = GenericPreprocessCollector(
        self._pre_obj, self._source_path,
        source_path_spec=self._source_path_spec)
    filter_object = BuildCollectionFilterFromFile(self._filter_file_path)

    for path_spec in preprocessor_collector.GetPathSpecs(filter_object):
      self.ProducePathSpec(path_spec)

  def _ProcessImage(self, volume_path_spec):
    """Processes a volume within a storage media image.

    Args:
      volume_path_spec: The path specification of the volume containing
                        the file system.
    """
    logging.debug(u'Collecting from image file: {0:s}'.format(
        self._source_path))

    if self._process_vss:
      self._hashlist = {}

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=volume_path_spec)

    try:
      root_file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
    except IOError as exception:
      logging.error((
          u'Unable to read file system in storage media image with error: '
          u'{0:s}').format(exception))
      return

    try:
      self._ProcessDirectory(root_file_entry)
    except (dfvfs_errors.AccessError, dfvfs_errors.BackEndError) as exception:
      logging.warning(u'{0:s}'.format(exception))
      logging.debug(u'Collection from image ABORTED.')
      return

    if self._process_vss:
      logging.info(u'Collecting from VSS.')

      vss_path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_VSHADOW, location=u'/',
          parent=volume_path_spec)

      vss_file_entry = path_spec_resolver.Resolver.OpenFileEntry(vss_path_spec)

      number_of_vss = vss_file_entry.number_of_sub_file_entries
      if self._vss_stores:
        vss_store_range = [store_nr - 1 for store_nr in self._vss_stores]
      else:
        vss_store_range = range(0, number_of_vss)

      for store_index in vss_store_range:
        logging.info(u'Collecting from VSS volume: {0:d} out of: {1:d}'.format(
            store_index + 1, number_of_vss))
        self._ProcessVss(volume_path_spec, store_index)

    logging.debug(u'Collection from image COMPLETED.')

  def _ProcessImageWithFilter(self, volume_path_spec):
    """Processes a volume within an image with the collection filter.

    Args:
      volume_path_spec: The path specification of the volume containing
                        the file system.
    """
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/',
        parent=volume_path_spec)

    # TODO: Change the preprocessor collector into a find function.
    preprocessor_collector = GenericPreprocessCollector(
        self._pre_obj, self._source_path, source_path_spec=path_spec)

    filter_object = BuildCollectionFilterFromFile(self._filter_file_path)

    for path_spec in preprocessor_collector.GetPathSpecs(filter_object):
      self.ProducePathSpec(path_spec)

    if self._process_vss:
      logging.debug(u'Searching for VSS')

      vss_path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_VSHADOW, location=u'/',
          parent=volume_path_spec)

      vss_file_entry = path_spec_resolver.Resolver.OpenFileEntry(vss_path_spec)

      number_of_vss = vss_file_entry.number_of_sub_file_entries

      if not self._vss_stores:
        list_of_vss_stores = range(0, number_of_vss)
      else:
        list_of_vss_stores = []

        for store_index in self._vss_stores:
          if store_index > 0 and store_index <= number_of_vss:
            # In plaso 1 represents the first store index in
            # pyvshadow 0 represents the first store index so 1 is subtracted.
            list_of_vss_stores.append(store_index - 1)

      for store_index in list_of_vss_stores:
        logging.info(
            u'Collecting from VSS volume: {0:d} out of: {1:d}'.format(
                store_index + 1, number_of_vss))

        # TODO: Change the preprocessor collector into a find function.
        vss_preprocessor_collector = GenericPreprocessCollector(
            self._pre_obj, self._source_path, source_path_spec=path_spec)
        vss_preprocessor_collector.SetVssInformation(store_index=store_index)
        filter_object = BuildCollectionFilterFromFile(self._filter_file_path)

        for path_spec in vss_preprocessor_collector.GetPathSpecs(
            filter_object):
          self.ProducePathSpec(path_spec)

    logging.debug(u'Targeted Image Collector - Done.')

  def _ProcessVss(self, volume_path_spec, store_index):
    """Processes a Volume Shadow Snapshot (VSS) in the image.

    Args:
      volume_path_spec: The path specification of the volume containing
                        the VSS.
      store_index: The VSS store index number.
    """
    logging.debug(u'Collecting from VSS store {0:d}'.format(store_index))

    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_VSHADOW, store_index=store_index,
        parent=volume_path_spec)
    path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_TSK, location=u'/', parent=path_spec)

    root_file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)

    try:
      self._ProcessDirectory(root_file_entry)
    except (dfvfs_errors.AccessError, dfvfs_errors.BackEndError) as exception:
      logging.warning(u'{0:s}'.format(exception))
      logging.debug(
          u'Collection from VSS store: {0:d} ABORTED.'.format(store_index))
      return

    logging.debug(
        u'Collection from VSS store: {0:d} COMPLETED.'.format(store_index))

  def Collect(self):
    """Collects files from the source."""
    source_file_entry = path_spec_resolver.Resolver.OpenFileEntry(
        self._source_path_spec)

    if not source_file_entry:
      logging.warning(u'No files to collect.')
      self.SignalEndOfInput()
      return

    if (not source_file_entry.IsDirectory() and
        not source_file_entry.IsFile() and
        not source_file_entry.IsDevice()):
      raise errors.CollectorError(
          u'Source path: {0:s} not a device, file or directory.'.format(
              self._source_path))

    type_indicator = self._source_path_spec.type_indicator
    if type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS:
      if self._filter_file_path:
        self._ProcessFileSystemWithFilter()

      elif source_file_entry.IsDirectory():
        try:
          self._ProcessDirectory(source_file_entry)
        except (dfvfs_errors.AccessError,
                dfvfs_errors.BackEndError) as exception:
          logging.warning(u'{0:s}'.format(exception))

      else:
        self.ProducePathSpec(self._source_path_spec)

    else:
      if self._filter_file_path:
        self._ProcessImageWithFilter(self._source_path_spec.parent)
      else:
        self._ProcessImage(self._source_path_spec.parent)

    self.SignalEndOfInput()

  def SetFilter(self, filter_file_path, pre_obj):
    """Sets the collection filter.

    Args:
      filter_file_path: The path of the filter file.
      pre_obj: The preprocessor object.
    """
    self._filter_file_path = filter_file_path
    self._pre_obj = pre_obj

  def SetVssInformation(self, vss_stores=None):
    """Sets the Volume Shadow Snapshots (VSS) information.

       This function will enable VSS collection.

    Args:
      vss_stores: Optional range of VSS stores to include in the collection.
                  Where 1 represents the first store. The default is None.
    """
    self._process_vss = True
    self._vss_stores = vss_stores


class GenericPreprocessCollector(object):
  """Class that implements a generic preprocess collector object."""

  _PATH_EXPANDER_RE = re.compile(r'^[{][a-z_]+[}]$')

  def __init__(self, pre_obj, source_path, source_path_spec=None):
    """Initializes the preprocess collector object.

    Args:
      pre_obj: The preprocessing object (instance of PreprocessObject).
      source_path: Path of the source file or directory.
      source_path_spec: Optional source path specification (instance of
                        dfvfs.PathSpec) as determined by the file system
                        scanner. The default is None.
    """
    super(GenericPreprocessCollector, self).__init__()
    self._byte_offset = None
    self._path_expander = winreg_path_expander.WinRegistryKeyPathExpander(
        pre_obj, None)
    self._process_image = None
    self._process_vss = None
    self._source_path = source_path
    self._source_path_spec = source_path_spec
    self._store_index = None

  def _GetExtendedPath(self, path):
    """Return an extened path without the generic path elements.

    Remove common generic path elements, like {log_path}, {windir}
    and extend them to their real meaning.

    Args:
      path: The path before extending it.

    Returns:
      A string containing the extended path.
    """
    try:
      return self._path_expander.ExpandPath(path)
    except KeyError as exception:
      logging.error(
          u'Unable to expand path {0:s} with error: {1:s}'.format(
              path, exception))

  def _GetPaths(self, path_segments_expressions_list):
    """Retrieves paths based on path segments expressions.

       A path segment expression is either a regular expression or a string
       containing an expanded path segment.

    Args:
       path_segments_expressions_list: A list of path segments expressions.

    Yields:
      The paths found.
    """
    path_spec = self._source_path_spec

    if (not path_spec or
        path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS):
      process_image = self._process_image
    else:
      process_image = True

    if process_image:
      path_spec = self._GetPathSpec(u'/')

    else:
      path_spec = path_spec_factory.Factory.NewPathSpec(
        dfvfs_definitions.TYPE_INDICATOR_OS, location=self._source_path)

    file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
    file_system = file_entry.GetFileSystem()

    if path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS:
      source_path = os.path.abspath(self._source_path)

      # When processing the file system strip off the path separator at
      # the end of the source path.
      if source_path.endswith(os.path.sep):
        source_path = source_path[:-1]

    paths_found = ['']
    for path_segment_expression in path_segments_expressions_list:
      sub_paths_found = []

      for path in paths_found:
        if path_spec.type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS:
          full_path = file_system.JoinPath([source_path, path])
        else:
          full_path = path

        if (path_spec.type_indicator != dfvfs_definitions.TYPE_INDICATOR_OS and
            not path):
          file_entry = file_system.GetRootFileEntry()

        else:
          # We need to pass only used arguments to the path specification
          # factory otherwise it will raise.
          kwargs = {}
          if path_spec.parent:
            kwargs['parent'] = path_spec.parent
          kwargs['location'] = full_path

          sub_path_spec = path_spec_factory.Factory.NewPathSpec(
              file_system.TYPE_INDICATOR, **kwargs)
          file_entry = path_spec_resolver.Resolver.OpenFileEntry(sub_path_spec)

        if not file_entry:
          logging.error((
              u'Unable to open sub file entry with path specification: '
              u'{0:s}').format(sub_path_spec.comparable))
          continue

        # Since there are more path segment expressions and the file entry
        # is not a directory this cannot be the path we're looking for.
        if not file_entry.IsDirectory():
          continue

        for sub_file_entry in file_entry.sub_file_entries:
          sub_file_entry_match = u''

          # TODO: need to handle case (in)sentive matches.
          if isinstance(path_segment_expression, basestring):
            if path_segment_expression == sub_file_entry.name:
              sub_file_entry_match = sub_file_entry.name

          else:
            re_match = path_segment_expression.match(sub_file_entry.name)

            if re_match:
              sub_file_entry_match = re_match.group(0)

          if sub_file_entry_match:
            sub_file_entry_match = file_system.JoinPath([
                path, sub_file_entry_match])

            sub_paths_found.append(sub_file_entry_match)

      paths_found = sub_paths_found

      if not paths_found:
        break

    for path in paths_found:
      if not path:
        # Make sure to represent the root as a path.
        path = file_system.PATH_SEPARATOR

      yield path

  def _GetPathSegmentExpressionsList(self, path_expression, path_separator):
    """Retrieves a list of paths  segment expressions on a path expression.

       A path segment expression is either a regular expression or a string
       containing an expanded path segment.

    Args:
      path_expression: The path expression, which is a string that can contain
                       system specific placeholders such as e.g. "{log_path}"
                       or "{windir}" or regular expressions such as e.g.
                       "[0-9]+" to match a path segments that only consists of
                       numeric values.
      path_separator: The path separator.

    Returns:
      A list of path segments expressions.
    """
    path_segments_expressions_list = []
    for path_segment in path_expression.split(path_separator):
      # Ignore empty path segments.
      if not path_segment:
        continue

      # TODO: add startswith('{') and endswith('}') to improve average
      # case performance here. Combine this with find rewrite.
      if self._PATH_EXPANDER_RE.match(path_segment):
        expression_list = self._GetExtendedPath(path_segment).split(u'/')
        if expression_list[0] == u'' and len(expression_list) > 1:
          expression_list = expression_list[1:]

        path_segments_expressions_list.extend(expression_list)

      else:
        try:
          # We compile the regular expression so it spans the full path
          # segment.
          expression_string = u'^{0:s}$'.format(path_segment)
          expression = re.compile(expression_string, re.I | re.S)

        except sre_constants.error as exception:
          error_string = (
              u'Unable to compile regular expression for path segment: {0:s} '
              u'with error: {1:s}').format(path_segment, exception)
          logging.warning(error_string)
          raise errors.PathNotFound(error_string)

        path_segments_expressions_list.append(expression)

    return path_segments_expressions_list

  def _GetPathSpec(self, path):
    """Retrieves the path specification."""
    if self._source_path_spec:
      type_indicator = self._source_path_spec.type_indicator
      if type_indicator == dfvfs_definitions.TYPE_INDICATOR_OS:
        # Note we cannot use os.path.join() here since it breaks on Windows
        # when path starts with a path separator.
        path = u'{0:s}{1:s}{2:s}'.format(self._source_path, os.path.sep, path)

      # We need to pass only used arguments to the path specification
      # factory otherwise it will raise.
      kwargs = {}
      if self._source_path_spec.parent:
        kwargs['parent'] = self._source_path_spec.parent
      kwargs['location'] = path

      path_spec = path_spec_factory.Factory.NewPathSpec(
          type_indicator, **kwargs)

    elif self._process_image:
      # If source path spec was not defined fallback on the old method.
      path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_OS, location=self._source_path)

      if self._byte_offset > 0:
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_TSK_PARTITION,
            start_offset=self._byte_offset, parent=path_spec)

      if self._process_vss:
        path_spec = path_spec_factory.Factory.NewPathSpec(
            dfvfs_definitions.TYPE_INDICATOR_VSHADOW,
            store_index=self._store_index, parent=path_spec)

      path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_TSK, location=path, parent=path_spec)

    else:
      # Note we cannot use os.path.join() here since it breaks on Windows
      # when path starts with a path separator.
      path = u'{0:s}{1:s}{2:s}'.format(self._source_path, os.path.sep, path)

      path_spec = path_spec_factory.Factory.NewPathSpec(
          dfvfs_definitions.TYPE_INDICATOR_OS, location=path)

    return path_spec

  def GetFilePaths(self, path_expression, filename_expression, path_separator):
    """Retrieves paths based on a path and filename expression.

    Args:
      path_expression: The path expression, which is a string that can contain
                       system specific placeholders such as e.g. "{log_path}"
                       or "{windir}" or regular expressions such as e.g.
                       "[0-9]+" to match a path segments that only consists of
                       numeric values.
      filename_expression: The filename expression.
      path_separator: The path separator.

    Returns:
      A list of paths.
    """
    path_segments_expressions_list = self._GetPathSegmentExpressionsList(
        path_expression, path_separator)

    path_segments_expressions_list.extend(
        self._GetPathSegmentExpressionsList(
            filename_expression, path_separator))

    return self._GetPaths(path_segments_expressions_list)

  def GetPathSpecs(self, collection_filter):
    """A generator yielding all pathspecs from the given filters."""
    list_of_filters = collection_filter.BuildFilters()

    for filter_path, filter_file in list_of_filters:
      try:
        paths = list(self.FindPaths(filter_path))

      except errors.PathNotFound as exception:
        logging.warning(u'Unable to find path: [{0:s}] {1:s}'.format(
            filter_path, exception))
        continue

      for path in paths:

        # TODO: dfVFS refactor, fix this in find rewrite.
        # TODO: Need to make sure "path" is a directory (easier using pyVFS
        # ideas). Until then have a quick "try" attempt, remove that once
        # proper stats are implemented.
        try:
          for file_path in self.GetFilePaths(path, filter_file, path[0]):
            path_spec = self._GetPathSpec(file_path)

            file_entry = path_spec_resolver.Resolver.OpenFileEntry(path_spec)
            if file_entry:
              yield file_entry.path_spec

        # TODO: dfVFS refactor, unlikely to be still raised.
        except errors.PreProcessFail as exception:
          logging.warning((
              u'Unable to parse filter: {0:s}/{1:s} - path not found '
              u'[{2:s}].').format(filter_path, filter_file, exception))
          continue

        # TODO: dfVFS refactor, this should be local to where it can be raised.
        except sre_constants.error:
          logging.warning((
              u'Unable to parse the filter: {0:s}/{1:s} - illegal regular '
              u'expression.').format(filter_path, filter_file))
          continue

  # TODO: in dfVFS create a separate FindExpression of FindSpec object to
  # define path expresssions.
  def FindPaths(self, path_expression):
    """Finds paths based on a path expression.

       An empty path expression will return all paths. Note that the path
       expression uses / as the path (segment) separator.

    Args:
      path_expression: The path expression, which is a string that can contain
                       system specific placeholders such as e.g. "{log_path}" or
                       "{windir}" or regular expressions such as e.g.
                       "[0-9]+" to match a path segments that only consists of
                       numeric values.

    Returns:
      A list of paths.

    Raises:
      errors.PathNotFound: If unable to compile any regular expression.
    """
    path_segments_expressions_list = self._GetPathSegmentExpressionsList(
        path_expression, u'/')

    return self._GetPaths(path_segments_expressions_list)

  def OpenFileEntry(self, path):
    """Opens a file entry object from the path."""
    path_spec = self._GetPathSpec(path)
    return path_spec_resolver.Resolver.OpenFileEntry(path_spec)

  def SetImageInformation(self, byte_offset):
    """Sets the image information.

       This function will enable image collection.

    Args:
      byte_offset: Byte offset into the image file.
    """
    self._process_image = True
    self._byte_offset = byte_offset

  def SetVssInformation(self, store_index=None):
    """Sets the Volume Shadow Snapshots (VSS) information.

       This function will enable VSS collection.

    Args:
      store_index: Optional VSS store index number. The default is None.
    """
    self._process_vss = True
    self._store_index = store_index


def BuildCollectionFilterFromFile(filter_file_path):
  """Returns a collection filter from a filter file."""
  filter_strings = []

  with open(filter_file_path, 'rb') as file_object:
    for line in file_object:
      line = line.strip()
      if line.startswith(u'#'):
        continue
      filter_strings.append(line)

  return event.CollectionFilter(filter_strings)
