#!/usr/bin/python
# -*- coding: utf-8 -*-
# Copyright 2012 Google Inc. All Rights Reserved.
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
"""The storage mechanism for Plaso.

The storage mechanism can be described as a collection of storage files
that are stored together in a single ZIP compressed container.

Each storage file contains several serialized events (as protobufs)
that are fully sorted. However, since the storage container can contain
more than one storage file the overall storage is not fully sorted.

The basic structure of a single storage file in Plaso is:
  plaso_meta.<seq_num>
  plaso_proto.<seq_num>
  plaso_index.<seq_num>

Where the meta file is a simple text file using YAML for variable
definition, example:
  variable: value
  a_list: [value, value, value]

This can be used to filter out which proto files should be included
in processing.

The index file contains an index to all the entries stored within
the protobuf file, so that it can be easily seeked. The layout is:

+-----+-----+-...+
| int | int | ...|
+-----+-----+-...+

Where int is an unsigned integer '<I' that represents the byte offset
into the .proto file where the beginning of the size variable lies.

This can be used to seek the proto file directly to read a particular
entry within the proto file.

Otherwise the structure of a proto file is:
+------+---------------------------------+------+------...+
| size |  protobuf (plaso_storage_proto) | size | proto...|
+------+---------------------------------+------+------...+

For further details about the storage design see:
https://sites.google.com/a/kiddaland.net/plaso/developer/libraries/storage
"""
import collections
import heapq
import logging
import struct
import sys
import zipfile
import yaml

from google.protobuf import message

from plaso.lib import errors
from plaso.lib import pfile
from plaso.lib import queue
from plaso.proto import plaso_storage_pb2
from plaso.proto import transmission_pb2


class PlasoStorage(object):
  """Abstract the storage reading and writing."""

  # Set the buffer size to 256Mb
  MAX_BUFFER_SIZE = 1024 * 1024 * 256

  # Set the version of this storage mechanism.
  STORAGE_VERSION = 1

  source_short_map = {}
  for value in plaso_storage_pb2.EventObject.DESCRIPTOR.enum_types_by_name[
      'SourceShort'].values:
    source_short_map[value.name] = value.number

  def __init__(self, output_file, buffer_size=0, read_only=False,
               pre_obj=None):
    """Constructor for PlasoStorage.

    Args:
      output_file: The name of the output file.
      buffer_size: The estimated size of a protobuf file.
      read_only: Indicate we are just opening up ZIP file for reading.
      pre_obj: A preprocessing object that gets stored inside the storage
      if defined.

    Raises:
      IOError: if we open up the file in read only mode and the file does
      not exist.
    """
    compression = zipfile.ZIP_DEFLATED

    self._filenumber = 1
    self._buffer = []
    self._buffer_size = 0
    self.protofiles = {}
    self._buffer_first_timestamp = sys.maxint
    self._buffer_last_timestamp = 0
    self._max_buffer_size = buffer_size or self.MAX_BUFFER_SIZE
    self._write_counter = 0
    self._pre_obj = pre_obj

    if read_only:
      mode = 'r'
    else:
      mode = 'a'

    try:
      self.zipfile = zipfile.ZipFile(output_file, mode, compression)
    except zipfile.BadZipfile as e:
      raise IOError('Not a ZIP file, cannot read. Error message: %s', e)
    self._file_open = True

    if not read_only:
      logging.debug('Writing to file. Buffer size used: %s',
                    self._max_buffer_size)

      if pre_obj:
        __pychecker__ = 'no-abstract'
        pre_obj.counter = collections.Counter()
        pre_obj.collection_information['cmd_line'] = u' '.join(sys.argv)

      # Need to get the last number in the list.
      for name in self.zipfile.namelist():
        if 'plaso_meta.' in name:
          _, number = name.split('.')
          if int(number) >= self._filenumber:
            self._filenumber = int(number) + 1

  def _StorePreObject(self, pre_obj):
    """Store information gathered during preprocessing to the storage file."""
    current_object = self.GetStorageInformation()
    if current_object:
      current_object.append(pre_obj)
    else:
      current_object = [pre_obj, ]  # pylint: disable=g-illegal-space

    self.zipfile.writestr('information.yaml', yaml.dump(current_object))

  def GetStorageInformation(self):
    """Return gathered preprocessing information from a storage file."""
    try:
      pre_file = self.zipfile.open('information.yaml', 'r')
      return yaml.load(pre_file)
    except KeyError:
      return None

  def GetEntry(self, number, entry=None):
    """Return a protobuf read from filehandle.

    By default the next entry in the appropriate proto file is read
    and returned, however any entry can be read using the index file.

    Args:
      number: The proto file number.
      entry: Read a specific entry in the file, otherwise the next one.

    Returns:
      A protobuf entry read from the file.

    Raises:
      EOFError: When we reach the end of the protobuf file.
    """
    if number in self.protofiles:
      fh = self.protofiles[number]
    else:
      fh = self.zipfile.open('plaso_proto.%06d' % number, 'r')
      self.protofiles[number] = fh

    if entry:
      # TODO: Add the possibility to seek a particular entry.
      # The problem here is that seeking to a file can be problematic
      # since it is stored within a ZIP container.
      # Extracting the file and then parsing it may serve as a quick
      # workaraound, yet these files may be 256Mb or larger so that isn't
      # perhaps what we would like to do.
      # The commented-out implementation below both does not work and is
      # very slow, it needs to be cached and handled properly.
      logging.error('This is not supported as of now.')
      return ''

    unpacked = fh.read(4)

    if len(unpacked) != 4:
      return None

    size = struct.unpack('<I', unpacked)[0]

    if size > 1024 * 1024 * 40:
      raise errors.WrongProtobufEntry('Protobuf size too large: %d', size)

    proto_serialized = fh.read(size)
    proto = plaso_storage_pb2.EventObject()
    proto.ParseFromString(proto_serialized)

    return proto

  def GetEntries(self, number):
    """A generator to read all plaso_storage protobufs from a filehandle.

    The storage mechanism of Plaso works in the way that it creates potentially
    several files inside the ZIP container. As soon as the number of protobufs
    stored exceed the size of buffer_size they will be flushed to disk as:

          plaso_proto.XXX

    Where XXX is an increasing integer, starting from one. To get all the files
    or the numbers that are available this class implements a method called
    GetProtoNumbers() that returns a list of all available protobuf files within
    the container.

    This method returns a generator that returns all plaso_storage protobufs in
    the named container, as indicated by the number argument. So if this method
    is called as storage_object.GetEntries(1) the generator will return the
    entries found in the file plaso_proto.000001.

    Args:
      number: The protofile number.

    Yields:
      A protobuf object from the protobuf file.
    """
    while True:
      try:
        proto = self.GetEntry(number)
        if not proto:
          logging.debug('End of protobuf file plaso_proto.%06d reached.',
                        number)
          break
        yield proto
      except errors.WrongProtobufEntry as e:
        logging.warning(('Problem while parsing a protobuf entry from: '
                         'plaso_proto.%06d <%s>'), number, e)

  def GetProtoNumbers(self):
    """Return all available protobuf numbers."""
    numbers = []
    for name in self.zipfile.namelist():
      if 'plaso_proto' in name:
        _, num = name.split('.')
        numbers.append(int(num))

    for number in sorted(numbers):
      yield number

  def ReadMeta(self, number):
    """Return a dict with the metadata entries.

    Args:
      number: The number of the metadata file (name is plaso_meta_XXX where
              XXX is this number.

    Returns:
      A dict object containing all the variables inside the metadata file.
    """
    meta_file = self.zipfile.open('plaso_meta.%06d' % number, 'r')
    return yaml.load(meta_file)

  def GetBufferSize(self):
    """Return the size of the buffer."""
    return self._buffer_size

  def GetFileNumber(self):
    return self._filenumber

  def AddEntry(self, event):
    """Add an entry into the buffer.

    Args:
      event: An EventObject to append to the buffer.

    Raises:
      IOError: When trying to write to a closed storage file.
    """
    if not self._file_open:
      raise IOError('Trying to add an entry to a closed storage file.')

    if event.timestamp > self._buffer_last_timestamp:
      self._buffer_last_timestamp = event.timestamp

    if event.timestamp < self._buffer_first_timestamp and event.timestamp > 0:
      self._buffer_first_timestamp = event.timestamp

    serialized = self.SerializeEvent(event)
    if not serialized:
      return

    # Add values to counters.
    if self._pre_obj:
      self._pre_obj.counter['total'] += 1
      self._pre_obj.counter[event.source_long] += 1

    heapq.heappush(self._buffer, (event.timestamp, serialized))
    self._buffer_size += len(serialized)
    self._write_counter += 1

    if self._buffer_size > self._max_buffer_size:
      self.FlushBuffer()

  def SerializeEvent(self, an_event):
    """Return a serialized event."""
    proto = plaso_storage_pb2.EventObject()
    for attr in an_event.GetAttributes():
      if attr == 'source_short':
        proto.source_short = self.source_short_map.get(
            an_event.source_short, 6)
      elif attr == 'pathspec':
        path = transmission_pb2.PathSpec()
        path.ParseFromString(an_event.pathspec)
        proto.pathspec.MergeFrom(path)
      elif hasattr(proto, attr):
        attribute_value = getattr(an_event, attr)
        if type(attribute_value) == str:
          attribute_value = pfile.GetUnicodeString(attribute_value)
        setattr(proto, attr, attribute_value)
      else:
        a = proto.attributes.add()
        a.key = attr
        a.value = pfile.GetUnicodeString(getattr(an_event, attr))
    try:
      return proto.SerializeToString()
    except message.EncodeError as e:
      logging.warning('Unable to serialize event (skip), error msg: %s', e)

    return ''

  def FlushBuffer(self):
    """Flush a buffer to disk."""

    if not self._buffer_size:
      return
    meta_fh = 'plaso_meta.%06d' % self._filenumber
    proto_fh = 'plaso_proto.%06d' % self._filenumber
    index_fh = 'plaso_index.%06d' % self._filenumber

    # TODO: Add more information into the meta file
    # that can be used for quick filtering data chunks.
    yaml_dict = {'range': (self._buffer_first_timestamp,
                           self._buffer_last_timestamp),
                 'version': self.STORAGE_VERSION}
    self.zipfile.writestr(meta_fh, yaml.dump(yaml_dict))

    ofs = 0
    proto_str = []
    index_str = []
    for _ in range(len(self._buffer)):
      _, entry = heapq.heappop(self._buffer)
      # TODO: Instead of appending to an array
      # which is not optimal (loads up the entire max file
      # size into memory) Zipfile should be extended to
      # allow appending to files (implement lock).
      index_str.append(struct.pack('<I', ofs))
      packed = struct.pack('<I', len(entry)) + entry
      ofs += len(packed)
      proto_str.append(packed)

    self.zipfile.writestr(index_fh, ''.join(index_str))
    self.zipfile.writestr(proto_fh, ''.join(proto_str))

    self._filenumber += 1
    self._buffer_size = 0
    self._buffer = []
    self._buffer_first_timestamp = sys.maxint
    self._buffer_last_timestamp = 0

  def CloseStorage(self):
    """Closes the storage, flush the last buffer and closes the ZIP file."""
    if self._file_open:
      if self._pre_obj:
        self._StorePreObject(self._pre_obj)
      self.FlushBuffer()
      self.zipfile.close()
      self._file_open = False
      logging.debug(('[Storage] Closing the storage, nr. of events processed:'
                     ' %d'), self._write_counter)

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.CloseStorage()

  def __enter__(self):
    """Make usable with "with" statement."""
    return self


class SimpleStorageDumper(object):
  """Watch a queue with EventObjects and process them for storage."""

  def __init__(self, output_file, buffer_size=0, pre=None):
    """Constructor for the storage.

    Args:
      output_file: The path to the output file.
      buffer_size: The estimated size of a protobuf file.
      pre: A pre-processing object.
    """
    self._queue = queue.SimpleQueue()
    self.output = output_file
    self.buffer_size = buffer_size
    self._pre_obj = pre

  def Run(self):
    """Start the storage."""
    with PlasoStorage(
        self.output, buffer_size=self.buffer_size,
        pre_obj=self._pre_obj) as storage_buffer:
      for item in self._queue.PopItems():
        storage_buffer.AddEntry(item)

  def AddEvent(self, item):
    self._queue.Queue(item)

  def Close(self):
    self._queue.Close()
