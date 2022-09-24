# -*- coding: utf-8 -*-
"""Analysis plugin to look up files in Viper and tag events.

Also see:
  https://viper-framework.readthedocs.io/en/latest/usage/web.html#api
"""

from plaso.analysis import hash_tagging
from plaso.analysis import logger
from plaso.analysis import manager
from plaso.containers import events
from plaso.lib import errors


class ViperAnalysisPlugin(hash_tagging.HashTaggingAnalysisPlugin):
  """An analysis plugin for looking up hashes in Viper."""

  # TODO: Check if there are other file types worth checking Viper for.
  DATA_TYPES = frozenset(['pe', 'pe:compilation:compilation_time'])

  NAME = 'viper'

  SUPPORTED_HASHES = frozenset(['md5', 'sha256'])

  SUPPORTED_PROTOCOLS = frozenset(['http', 'https'])

  def __init__(self):
    """Initializes a Viper analysis plugin."""
    super(ViperAnalysisPlugin, self).__init__()
    self._host = None
    self._port = None
    self._protocol = None
    self._url = None

  def _Analyze(self, hashes):
    """Looks up hashes in Viper using the Viper HTTP API.

    Args:
      hashes (list[str]): hashes to look up.

    Returns:
      list[HashAnalysis]: hash analysis.

    Raises:
      RuntimeError: If no host has been set for Viper.
    """
    hash_analyses = []
    for digest in hashes:
      json_response = self._QueryHash(digest)
      hash_analysis = hash_tagging.HashAnalysis(digest, json_response)
      hash_analyses.append(hash_analysis)

    return hash_analyses

  def _GenerateLabels(self, hash_information):
    """Generates a list of labels that will be used in the event tag.

    Args:
      hash_information (dict[str, object]): JSON decoded contents of the result
          of a Viper lookup, as produced by the ViperAnalyzer.

    Returns:
      list[str]: list of labels to apply to events.
    """
    if not hash_information:
      return ['viper_not_present']

    projects = []
    tags = []
    for project, entries in hash_information.items():
      if not entries:
        continue

      projects.append(project)

      for entry in entries:
        if entry['tags']:
          tags.extend(entry['tags'])

    if not projects:
      return ['viper_not_present']

    labels = ['viper_present']
    for project_name in projects:
      label = events.EventTag.CopyTextToLabel(
          project_name, prefix='viper_project_')
      labels.append(label)

    for tag_name in tags:
      label = events.EventTag.CopyTextToLabel(tag_name, prefix='viper_tag_')
      labels.append(label)

    return labels

  def _QueryHash(self, digest):
    """Queries the Viper Server for a specific hash.

    Args:
      digest (str): hash to look up.

    Returns:
      dict[str, object]: JSON response or None on error.
    """
    if not self._url:
      self._url = '{0:s}://{1:s}:{2:d}/file/find'.format(
          self._protocol, self._host, self._port)

    request_data = {self._lookup_hash: digest}

    try:
      json_response = self._MakeRequestAndDecodeJSON(
          self._url, 'POST', data=request_data)

    except errors.ConnectionError as exception:
      json_response = None
      logger.error('Unable to query Viper with error: {0!s}.'.format(
          exception))

    return json_response

  def SetHost(self, host):
    """Sets the address or hostname of the server running Viper server.

    Args:
      host (str): IP address or hostname to query.
    """
    self._host = host

  def SetPort(self, port):
    """Sets the port where Viper server is listening.

    Args:
      port (int): port to query.
    """
    self._port = port

  def SetProtocol(self, protocol):
    """Sets the protocol that will be used to query Viper.

    Args:
      protocol (str): protocol to use to query Viper. Either 'http' or 'https'.

    Raises:
      ValueError: if the protocol is not supported.
    """
    protocol = protocol.lower().strip()
    if protocol not in self.SUPPORTED_PROTOCOLS:
      raise ValueError('Unsupported protocol: {0!s}'.format(protocol))

    self._protocol = protocol

  def TestConnection(self):
    """Tests the connection to the Viper server.

    Returns:
      bool: True if the Viper server instance is reachable.
    """
    url = '{0:s}://{1:s}:{2:d}/test'.format(
        self._protocol, self._host, self._port)

    try:
      json_response = self._MakeRequestAndDecodeJSON(url, 'GET')
    except errors.ConnectionError:
      json_response = None

    return json_response is not None


manager.AnalysisPluginManager.RegisterPlugin(ViperAnalysisPlugin)
