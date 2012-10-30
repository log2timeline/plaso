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
"""The main engine, the backbone that glues plaso together.

This can currently be looked as an alpha stage.

This file contains the main engine used by plaso or the main glue
that holds everything in one place.
"""
import logging
import multiprocessing
import os
import pdb
import sys
import time
import traceback

import pytz
import pyvshadow

from plaso import preprocessors

from plaso.lib import collector
from plaso.lib import errors
from plaso.lib import preprocess
from plaso.lib import queue
from plaso.lib import storage
from plaso.lib import vss
from plaso.lib import worker


def GetTimeZoneList():
  """Generates a list of all supported time zones."""
  yield 'local'
  for zone in pytz.all_timezones:
    yield zone


class Engine(object):
  """The main engine of plaso, the one that rules them all."""

  def __init__(self, config, event_filter=None):
    """Initialize the Plaso engine.

    Initializes some variables used in the tool as well
    as going over the configuration and veryfing each one.

    Args:
      config: A configuration object, either an optparse or an argparse one.
      event_filter: A filter object used to filter the output.

    Raises:
      errors.BadConfigOption: If the configuration options are wrong.
    """

    # TODO: Do something with the event_filter, that is
    # build an event filter that can be used to actually filter
    # out events and pass them to the needed modules for
    # additional processing.
    self.event_filter = event_filter

    self.worker_threads = []
    self.config = config

    # Do some initial verification here.
    if not os.path.isfile(config.filename) and not os.path.isdir(
        config.filename) and not (
            os.path.exists(config.filename) and config.image):
      raise errors.BadConfigOption(
          'File [%s] does not exist.' % config.filename)

    if os.path.isfile(config.output):
      logging.warning('Appending to an already existing file.')

    dirname = os.path.dirname(config.output)
    if not dirname:
      dirname = '.'

    if not os.access(dirname, os.W_OK):
      raise errors.BadConfigOption(
          'Unable to write to location: %s' % config.output)

    self.config.zone = pytz.timezone(config.tzone)

    if self.config.image:
      self.config.preprocess = True

  def _GuessOS(self, col_obj):
    """Return a guess for the OS we are pre-processing."""
    try:
      if col_obj.FindPath('/(Windows|WINNT)/System32'):
        return 'Windows'
    except errors.PathNotFound:
      pass

    try:
      if col_obj.FindPath('/System/Library'):
        return 'OSX'
    except errors.PathNotFound:
      pass

    try:
      if col_obj.FindPath('/etc'):
        return 'Linux'
    except errors.PathNotFound:
      pass

    return 'None'

  def _PreProcess(self, pre_obj):
    """Run the preprocessors."""

    logging.info('Starting to collect pre-processing information.')
    logging.info('Filename: %s', self.config.filename)

    if self.config.image:
      ofs = self.config.image_offset_bytes or self.config.image_offset * 512
      pre_collector = preprocess.TSKFileCollector(
          pre_obj, self.config.filename, ofs)
    elif self.config.recursive:
      pre_collector = preprocess.FileSystemCollector(
          pre_obj, self.config.filename)
    else:
      return

    if not hasattr(self.config, 'os'):
      self.config.os = self._GuessOS(pre_collector)

    plugin_list = preprocessors.PreProcessList(pre_obj, pre_collector)

    for weight in plugin_list.GetWeightList(self.config.os):
      for plugin in plugin_list.GetWeight(self.config.os, weight):
        plugin.Run()

    # Set the timezone.
    if hasattr(pre_obj, 'time_zone_str'):
      logging.info(u'Timezone set to: %s', pre_obj.time_zone_str)
      pre_obj.zone = pytz.timezone(
          getattr(pre_obj, 'time_zone_str'))
    else:
      pre_obj.zone = self.config.zone

  def Start(self):
    """Start the process, set up all processing."""

    if self.config.single_thread:
      logging.info('Starting the tool in a single thread.')
      try:
        self._StartSingleThread()
      except Exception as e:    # pylint: disable=W0703
        # The tool should generally not be run in single threaded mode
        # for other reasons than to debug. Hence the general error
        # catching.
        logging.error('An uncaught exception occured: %s.\n%s', e,
                      traceback.format_exc())
        if self.config.debug:
          pdb.post_mortem()
      return

    if self.config.local:
      logging.debug('Starting a local instance.')
      self._StartLocal()
      return

    logging.error('This version only supports local instance.')
    # TODO: Implement a more distributed version that is
    # scalable. That way each part of the tool can be run in a separate
    # machine.

  def _StartSingleThread(self):
    """Start everything up in a single thread.

    This should not normally be used, since running the tool in a single
    thread buffers up everything into memory until the storage is called.

    Just to make it clear, this starts up the collection, completes that
    before calling the worker that extracts all EventObjects and stores
    them in memory. when that is all done, the storage function is called
    to drain the buffer. Hence the tool's excessive use of memory in this
    mode and the reason why it is not suggested to be used except for
    debugging reasons (and mostly to get into the debugger).

    This is therefore mostly useful during debugging sessions for some
    limited parsing.
    """
    pre_obj = preprocess.PlasoPreprocess()

    if self.config.preprocess:
      self._PreProcess(pre_obj)
    else:
      pre_obj.zone = self.config.zone

    collection_queue = queue.SingleThreadedQueue()
    storage_queue = queue.SingleThreadedQueue()

    # Save some information about the run time into the pre-processing object.
    self._StoreCollectionInformation(pre_obj)

    # Start with collection.
    logging.debug('Starting collection.')
    with collector.PCollector(collection_queue) as my_collector:
      if self.config.image:
        ofs = self.config.image_offset_bytes or self.config.image_offset * 512
        my_collector.CollectFromImage(self.config.filename, ofs)
        if self.config.parse_vss:
          logging.debug('Parsing VSS from image.')
          volume = pyvshadow.volume()
          fh = vss.VShadowVolume(self.config.filename, ofs)
          vss_numbers = 0
          try:
            volume.open_file_object(fh)
            vss_numbers = volume.number_of_stores
          except IOError as e:
            logging.warning('Error while trying to read VSS: %s', e)
          for store_nr in range(0, vss_numbers):
            my_collector.CollectFromVss(
                self.config.filename, store_nr, ofs)
      elif self.config.recursive:
        my_collector.CollectFromDir(self.config.filename)
      else:
        my_collector.ProcessFile(self.config.filename, collection_queue)

    logging.debug('Collection done.')

    self.queues = [storage_queue, collection_queue]
    self.worker_threads = []

    logging.debug('Starting worker.')
    # Start processing entries.
    my_worker = worker.PlasoWorker(
        collection_queue, storage_queue, self.config, pre_obj)
    my_worker.Run()
    logging.debug('Worker process done.')

    # End with the storage.
    logging.debug('Starting storage.')
    with storage.PlasoStorage(self.config.output,
                              buffer_size=self.config.buffer_size,
                              pre_obj=pre_obj) as storage_buffer:
      for item in storage_queue.PopItems():
        storage_buffer.AddEntry(item)
    logging.debug('Storage done.')

  def _StartLocal(self):
    """Start the process, set up all threads and start them up.

    The local implementation uses the muliprocessing library to
    start up new threads or processes.
    """
    logging.info('Starting to extract events.')

    pre_obj = preprocess.PlasoPreprocess()
    # Run pre-processing if necessary.
    if self.config.preprocess:
      logging.info('Starting to preprocess.')
      self._PreProcess(pre_obj)
    else:
      pre_obj.zone = self.config.zone

    # Save some information about the run time into the pre-processing object.
    self._StoreCollectionInformation(pre_obj)

    # Start the collector.
    start_collection_thread = True
    if self.config.image:
      logging.debug('Collection started from an image.')
      my_collector = collector.SimpleImageCollector(
          self.config.filename, offset=self.config.image_offset,
          offset_bytes=self.config.image_offset_bytes,
          parse_vss=self.config.parse_vss)
    elif self.config.recursive:
      logging.debug('Collection started from a directory.')
      my_collector = collector.SimpleFileCollector(self.config.filename)
    else:
      # If we are parsing a single file we don't want to start a separate
      # thread for the collection, hence this variable.
      start_collection_thread = False
      self.config.workers = 1

      # We need to make sure we are dealing with a file.
      if not os.path.isfile(self.config.filename):
        raise errors.BadConfigOption(
            'Wrong usage: {%s} has to be a file.' % self.config.filename)

      # Need to manage my own queueing since we are not starting a formal
      # collector.
      my_collector = queue.SimpleQueue()
      a_collector = collector.PCollector(my_collector)
      a_collector.ProcessFile(self.config.filename, my_collector)
      my_collector.Close()

    my_storage = storage.SimpleStorageDumper(
        self.config.output, self.config.buffer_size, pre_obj)

    self.queues = [my_collector, my_storage]

    # Start the storage.
    logging.debug('Starting storage.')
    self.storage_thread = multiprocessing.Process(
        name='StorageThread',
        target=my_storage.Run)
    self.storage_thread.start()

    logging.debug('Starting collection.')
    if start_collection_thread:
      self.collection_thread = multiprocessing.Process(
          name='Collection',
          target=my_collector.Run)
      self.collection_thread.start()

    # Start workers.
    logging.debug('Starting workers.')
    for worker_nr in range(self.config.workers):
      logging.debug('Starting worker: %d', worker_nr)
      my_worker = worker.PlasoWorker(
          my_collector, my_storage, self.config, pre_obj)
      self.worker_threads.append(multiprocessing.Process(
          name='Worker_%d' % worker_nr,
          target=my_worker.Run))
      self.worker_threads[-1].start()

    # Wait until threads complete their work.
    logging.debug('Waiting for collection to complete.')
    if start_collection_thread:
      self.collection_thread.join()
    logging.debug('Collection is hereby DONE')

    logging.debug('Waiting until all workers complete their work.')
    for thread in self.worker_threads:
      thread.join()

    logging.debug('Workers are done, waiting for storage.')
    my_storage.Close()
    self.storage_thread.join()
    logging.debug('Storage process is done.')

  def _StoreCollectionInformation(self, obj):
    """Store information about collection into an object."""
    obj.collection_information = {}

    obj.collection_information['configured_zone'] = self.config.zone
    obj.collection_information['file_processed'] = self.config.filename
    obj.collection_information['output_file'] = self.config.output
    obj.collection_information['protobuf_size'] = self.config.buffer_size
    obj.collection_information['time_of_run'] = time.time()

    obj.collection_information['preprocess'] = str(
        bool(self.config.preprocess))

    obj.collection_information['recursive'] = str(
        bool(self.config.recursive))
    obj.collection_information['debug'] = str(
        bool(self.config.debug))
    obj.collection_information['vss parsing'] = str(
        bool(self.config.parse_vss))

    obj.collection_information['os_detected'] = getattr(
        self.config, 'os', 'N/A')

    if self.config.image:
      obj.collection_information['method'] = 'imaged processed'
      ofs = self.config.image_offset_bytes or self.config.image_offset * 512
      obj.collection_information['image_offset'] = ofs
    else:
      obj.collection_information['method'] = 'OS collection'

    if self.config.single_thread:
      obj.collection_information['runtime'] = 'single threaded'
    else:
      obj.collection_information['runtime'] = 'multi threaded'
      obj.collection_information['workers'] = self.config.workers

  def StopThreads(self):
    """Signals the tool to stop running nicely."""
    if self.config.single_thread and self.config.debug:
      logging.warning('Running in debug mode, set up debugger.')
      pdb.post_mortem()
      return

    logging.warning('Draining queues.')

    # TODO: Rewrite this so it makes more sense
    # and does a more effective job at stopping processes.
    for q in self.queues:
      q.Close()

    # Kill the collection thread.
    if hasattr(self, 'collection_thread'):
      logging.warning('Terminating the collection thread.')
      self.collection_thread.terminate()

    try:
      logging.warning('Waiting for workers to complete.')
      for t in self.worker_threads:
        t.join()
      logging.warning('Workers completed.')
      if hasattr(self, 'storage_thread'):
        logging.warning('Waiting for storage.')
        self.storage_thread.join()
        logging.warning('Storage ended.')

    except KeyboardInterrupt:
      logging.warning('Terminating all processes.')
      for t in self.worker_threads:
        t.terminate()
      logging.warning('Workers terminated.')
      if hasattr(self, 'storage_thread'):
        self.storage_thread.terminate()
        logging.warning('Storage terminated.')
      sys.exit(1)

