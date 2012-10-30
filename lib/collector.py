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
"""This is a file collector for Plaso, finding files needed to be parsed.

The classes here are used to fill a queue of PathSpec protobufs that need
to be further processed by the tool.
"""
import logging
import os

import pytsk3
import pyvshadow

from plaso.lib import pfile
from plaso.lib import queue
from plaso.lib import vss
from plaso.proto import transmission_pb2


class PCollector(object):
  """The Plaso Collector that scans for files needed to be processed."""

  def __init__(self, proc_queue):
    """Initialize the Plaso Collector.

    Args:
      proc_queue: A Plaso queue like object to store PathSpec protobufs in.
    """
    self._queue = proc_queue

  def CollectFromDir(self, directory):
    """Recursive traversal of a directory.

    Args:
      directory: The path to the directory to be parsed.
      to determine if they contain other files, read files within compressed.
    """
    for root, _, files in os.walk(directory):
      for filename in files:
        try:
          path = os.path.join(root, filename)
          if os.path.isfile(path):
            self.ProcessFile(path, self._queue)
        except IOError as e:
          logging.warning('Unable to further process %s:%s', filename, e)

  def CollectFromVss(self, image_path, store_nr, offset=0):
    """Collect files from a VSS image.

    Args:
      image_path: The path to the TSK image in the filesystem.
      store_nr: The store number for the VSS store.
      offset: An offset into the disk image to where the volume
      lies (sector size, not byte).
    """
    logging.debug('Collecting from VSS store %d', store_nr)

    fs = pfile.FilesystemCache.Open(image_path, offset, store_nr)

    self.ParseImageDir(fs, fs.fs.info.root_inum, '/')
    logging.debug('Collection from VSS store: %d COMPLETED.', store_nr)

  def CollectFromImage(self, image=None, offset=0):
    """Start the collector as an image collector.

    This collector goes over an image using pytsk.

    Args:
      image: The path to the image that needs to be opened.
      offset: An integer, a byte offset into the partition.
    """

    logging.debug(u'Collecting from an image file [%s]', image)

    fs = pfile.FilesystemCache.Open(image, offset)

    # read the root dir, and move from there
    self.ParseImageDir(fs, fs.fs.info.root_inum, '/')

  def ParseImageDir(self, fs, cur_inode, path):
    """A recursive traversal of a directory inside an image file.

    Recursive traversal through a directory that injects every file
    that is detected into the processing queue.

    Args:
      fs: A CacheFileSystem object that contains information about the
      filesystem being used to collect from.
      cur_inode: The inode number in which the directory begins.
      path: The full path name of the directory (string).
    """
    directory = fs.fs.open_dir(inode=cur_inode)
    for f in directory:
      try:
        name = f.info.name.name
        if not f.info.meta:
          continue
        inode_addr = f.info.meta.addr
        f_type = f.info.meta.type
      except AttributeError as e:
        logging.error('[ParseImage] Problem reading file [%s], error: %s',
                      name, e)
        continue

      # List of files we do not want to process further.
      if name in ['$OrphanFiles', '.', '..']:
        continue

      # We only care about regular files and directories
      if f_type == pytsk3.TSK_FS_META_TYPE_DIR:
        self.ParseImageDir(fs, inode_addr, os.path.join(path, name))
      elif f_type == pytsk3.TSK_FS_META_TYPE_REG:
        transfer_proto = transmission_pb2.PathSpec()
        if fs.store_nr >= 0:
          transfer_proto.type = transmission_pb2.PathSpec.VSS
          transfer_proto.vss_store_number = fs.store_nr
        else:
          transfer_proto.type = transmission_pb2.PathSpec.TSK
        transfer_proto.container_path = fs.path
        transfer_proto.image_offset = fs.offset
        transfer_proto.image_inode = inode_addr
        file_path = os.path.join(path, name)
        transfer_proto.file_path = pfile.GetUnicodeString(file_path)

        self._queue.Queue(transfer_proto.SerializeToString())

  def ProcessFile(self, filename, my_queue):
    """Finds all files available inside a file and inserts into queue."""
    transfer_proto = transmission_pb2.PathSpec()
    transfer_proto.type = transmission_pb2.PathSpec.OS
    transfer_proto.file_path = pfile.GetUnicodeString(filename)
    my_queue.Queue(transfer_proto.SerializeToString())

  def Close(self):
    self._queue.Close()

  def __exit__(self, unused_type, unused_value, unused_traceback):
    """Make usable with "with" statement."""
    self.Close()

  def __enter__(self):
    """Make usable with "with" statement."""
    return self


class SimpleFileCollector(queue.SimpleQueue):
  """This is a simple collector that collects from a directory."""

  def __init__(self, directory):
    """Initialize the file collector.

    Args:
      directory: Path to the directory that contains files to be collected.
    """
    super(SimpleFileCollector, self).__init__()
    self._dir = directory

  def Run(self):
    """Start the collection."""
    with PCollector(self) as my_collector:
      my_collector.CollectFromDir(self._dir)


class SimpleImageCollector(queue.SimpleQueue):
  """This is a simple collector that collects from an image file."""

  SECTOR_SIZE = 512

  def __init__(self, image, offset=0, offset_bytes=0, parse_vss=False):
    """Initialize the image collector.

    Args:
      image: A full path to the image file.
      offset: An offset into the image file if this is a disk image (in sector
      size, not byte size).
      offset_bytes: A bytes offset into the image file if this is a disk image.
      parse_vss: Boolean determining if we should collect from VSS as well
      (only applicaple in Windows with Volume Shadow Snapshot).
    """
    super(SimpleImageCollector, self).__init__()
    self._image = image
    self._offset = offset
    self._offset_bytes = offset_bytes
    self._vss = parse_vss

  def Run(self):
    """Start the collection."""
    with PCollector(self) as my_collector:
      offset = self._offset_bytes or self._offset * self.SECTOR_SIZE
      my_collector.CollectFromImage(self._image, offset)

      if self._vss:
        logging.debug('Searching for VSS')
        volume = pyvshadow.volume()
        fh = vss.VShadowVolume(self._image, offset)
        vss_numbers = 0
        try:
          volume.open_file_object(fh)
          vss_numbers = volume.number_of_stores
        except IOError as e:
          logging.warning('Error while trying to read VSS information: %s', e)
        for store_nr in range(0, vss_numbers):
          my_collector.CollectFromVss(self._image, store_nr, offset)

    logging.debug('Simple Image Collector - Done.')
