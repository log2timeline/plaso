# -*- coding: utf-8 -*-
"""Analysis plugin to look up file hashes in nsrlsvr and tag events."""

import socket

from plaso.analysis import hash_tagging
from plaso.analysis import logger
from plaso.analysis import manager


class NsrlsvrAnalysisPlugin(hash_tagging.HashTaggingAnalysisPlugin):
  """Analysis plugin for looking up hashes in nsrlsvr."""

  # The NSRL contains files of all different types, and can handle a high load
  # so look up all files.
  DATA_TYPES = frozenset(['fs:stat', 'fs:stat:ntfs'])

  NAME = 'nsrlsvr'

  SUPPORTED_HASHES = frozenset(['md5', 'sha1'])

  DEFAULT_LABEL = 'nsrl_present'

  _RECEIVE_BUFFER_SIZE = 4096

  _SOCKET_TIMEOUT = 3

  def __init__(self):
    """Initializes an nsrlsvr analysis plugin."""
    super(NsrlsvrAnalysisPlugin, self).__init__()
    self._host = None
    self._label = self.DEFAULT_LABEL
    self._port = None

  def _Analyze(self, hashes):
    """Looks up file hashes in nsrlsvr.

    Args:
      hashes (list[str]): hash values to look up.

    Returns:
      list[HashAnalysis]: analysis results, or an empty list on error.
    """
    logger.debug('Opening connection to {0:s}:{1:d}'.format(
        self._host, self._port))

    nsrl_socket = self._GetSocket()
    if not nsrl_socket:
      self.SignalAbort()
      return []

    hash_analyses = []
    for digest in hashes:
      response = self._QueryHash(nsrl_socket, digest)
      if response is not None:
        hash_analysis = hash_tagging.HashAnalysis(digest, response)
        hash_analyses.append(hash_analysis)

    nsrl_socket.close()

    logger.debug('Closed connection to {0:s}:{1:d}'.format(
        self._host, self._port))

    return hash_analyses

  def _GenerateLabels(self, hash_information):
    """Generates a list of strings that will be used in the event tag.

    Args:
      hash_information (bool): response from the hash tagging that indicates
          that the file hash was present or not.

    Returns:
      list[str]: list of labels to apply to event.
    """
    if hash_information:
      return [self._label]

    # TODO: Renable when tagging is removed from the analysis report.
    # return ['nsrl_not_present']
    return []

  def _GetSocket(self):
    """Establishes a connection to an nsrlsvr instance.

    Returns:
      socket._socketobject: socket connected to an nsrlsvr instance or None if
          a connection cannot be established.
    """
    try:
      connected_socket = socket.create_connection(
          (self._host, self._port), self._SOCKET_TIMEOUT)

    except socket.error as exception:
      connected_socket = None
      logger.error('Unable to connect to nsrlsvr with error: {0!s}.'.format(
          exception))

    return connected_socket

  def _QueryHash(self, nsrl_socket, digest):
    """Queries nsrlsvr for a specific hash.

    Args:
      nsrl_socket (socket._socketobject): socket of connection to nsrlsvr.
      digest (str): hash to look up.

    Returns:
      bool: True if the hash was found, False if not or None on error.
    """
    try:
      query = 'QUERY {0:s}\n'.format(digest).encode('ascii')
    except UnicodeDecodeError:
      logger.error('Unable to encode digest: {0!s} to ASCII.'.format(digest))
      return False

    response = None

    try:
      nsrl_socket.sendall(query)
      response = nsrl_socket.recv(self._RECEIVE_BUFFER_SIZE)

    except socket.error as exception:
      logger.error('Unable to query nsrlsvr with error: {0!s}.'.format(
          exception))

    if not response:
      return False

    # Strip end-of-line characters since they can differ per platform on which
    # nsrlsvr is running.
    response = response.strip()
    # nsrlsvr returns "OK 1" if the has was found or "OK 0" if not.
    return response == b'OK 1'

  def SetLabel(self, label):
    """Sets the tagging label.

    Args:
      label (str): label to apply to events extracted from files that are
          present in nsrlsvr.
    """
    self._label = label

  def SetHost(self, host):
    """Sets the address or hostname of the server running nsrlsvr.

    Args:
      host (str): IP address or hostname to query.
    """
    self._host = host

  def SetPort(self, port):
    """Sets the port where nsrlsvr is listening.

    Args:
      port (int): port to query.
    """
    self._port = port

  def TestConnection(self):
    """Tests the connection to nsrlsvr.

    Checks if a connection can be set up and queries the server for the
    MD5 of an empty file and expects a response. The value of the response
    is not checked.

    Returns:
      bool: True if nsrlsvr instance is reachable.
    """
    response = None
    nsrl_socket = self._GetSocket()
    if nsrl_socket:
      response = self._QueryHash(
          nsrl_socket, 'd41d8cd98f00b204e9800998ecf8427e')
      nsrl_socket.close()

    return response is not None


manager.AnalysisPluginManager.RegisterPlugin(NsrlsvrAnalysisPlugin)
