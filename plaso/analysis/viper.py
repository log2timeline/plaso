# -*- coding: utf-8 -*-
"""Analysis plugin to look up files in Viper and tag events."""

import logging

from plaso.analysis import interface
from plaso.analysis import manager
from plaso.containers import events
from plaso.lib import errors


class ViperAnalyzer(interface.HTTPHashAnalyzer):
  """Class that analyzes file hashes by consulting Viper."""

  _VIPER_API_PATH = u'file/find'
  _SUPPORTED_PROTOCOLS = frozenset([u'http', u'https'])

  def __init__(self, hash_queue, hash_analysis_queue, **kwargs):
    """Initializes a Viper hash analyzer.

    Args:
      hash_queue (Queue.queue): contains hashes to be analyzed.
      hash_analysis_queue (Queue.queue): that the analyzer will append
          HashAnalysis objects this queue.
    """
    super(ViperAnalyzer, self).__init__(
        hash_queue, hash_analysis_queue, **kwargs)
    self._checked_for_old_python_version = False
    self._host = None
    self._port = None
    self._protocol = None

  def Analyze(self, hashes):
    """Looks up hashes in Viper using the Viper HTTP API.

    The API is documented here:
      https://viper-framework.readthedocs.org/en/latest/usage/web.html#api

    Args:
      hashes: A list of hashes (strings) to look up. The Viper plugin supports
              only one hash at a time.

    Returns:
      A list of hash analysis objects (instances of HashAnalysis).

    Raises:
      RuntimeError: If no host has been set for Viper.
      ValueError: If the hashes list contains a number of hashes other than
                      one.
    """
    if not self._host:
      raise RuntimeError(u'No host specified for Viper lookup.')

    if len(hashes) != 1:
      raise ValueError(
          u'Unsupported number of hashes provided. Viper supports only one '
          u'hash at a time.')
    sha256 = hashes[0]

    hash_analyses = []
    url = u'{0:s}://{1:s}:{2:d}/{3:s}'.format(
        self._protocol, self._host, self._port, self._VIPER_API_PATH)
    params = {u'sha256': sha256}
    try:
      json_response = self.MakeRequestAndDecodeJSON(url, u'POST', data=params)
    except errors.ConnectionError as exception:
      logging.error(
          (u'Error communicating with Viper {0:s}. Viper plugin is '
           u'aborting.').format(exception))
      self.SignalAbort()
      return hash_analyses

    hash_analysis = interface.HashAnalysis(sha256, json_response)
    hash_analyses.append(hash_analysis)
    return hash_analyses

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
      ValueError: If an invalid protocol is specified.
    """
    protocol = protocol.lower().strip()
    if protocol not in self._SUPPORTED_PROTOCOLS:
      raise ValueError(u'Invalid protocol specified for Viper lookup')
    self._protocol = protocol


class ViperAnalysisPlugin(interface.HashTaggingAnalysisPlugin):
  """An analysis plugin for looking up SHA256 hashes in Viper."""

  # TODO: Check if there are other file types worth checking Viper for.
  DATA_TYPES = [u'pe:compilation:compilation_time']

  URLS = [u'https://viper.li']

  NAME = u'viper'

  def __init__(self):
    """Initializes a Viper analysis plugin."""
    super(ViperAnalysisPlugin, self).__init__(ViperAnalyzer)

  def GenerateLabels(self, hash_information):
    """Generates a list of strings that will be used in the event tag.

    Args:
      hash_information (dict[str, object]): JSON decoded contents of the result
          of a Viper lookup, as produced by the ViperAnalyzer.

    Returns:
      list[str]: list of labels to apply to events.
    """
    if not hash_information:
      return [u'viper_not_present']

    projects = []
    tags = []
    for project, entries in iter(hash_information.items()):
      if not entries:
        continue

      projects.append(project)

      for entry in entries:
        if entry[u'tags']:
          tags.extend(entry[u'tags'])

    if not projects:
      return [u'viper_not_present']
    strings = [u'viper_present']

    for project_name in projects:
      label = events.EventTag.CopyTextToLabel(
          project_name, prefix=u'viper_project_')
      strings.append(label)

    for tag_name in tags:
      label = events.EventTag.CopyTextToLabel(tag_name, prefix=u'viper_tag_')
      strings.append(label)

    return strings

  def SetHost(self, host):
    """Sets the address or hostname of the server running Viper server.

    Args:
      host (str): IP address or hostname to query.
    """
    self._analyzer.SetHost(host)

  def SetPort(self, port):
    """Sets the port where Viper server is listening.

    Args:
      port (int): port to query.
    """
    self._analyzer.SetPort(port)

  def SetProtocol(self, protocol):
    """Sets the protocol that will be used to query Viper.

    Args:
      protocol (str): protocol to use to query Viper. Either 'http' or 'https'.

    Raises:
      ValueError: If an invalid protocol is selected.
    """
    protocol = protocol.lower().strip()
    if protocol not in [u'http', u'https']:
      raise ValueError(u'Invalid protocol specified for Viper lookup')
    self._analyzer.SetProtocol(protocol)


manager.AnalysisPluginManager.RegisterPlugin(ViperAnalysisPlugin)
