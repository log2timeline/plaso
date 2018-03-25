"""Script to create Jenkins Slaves."""

from __future__ import print_function
from __future__ import unicode_literals

import argparse
import json
import sys
import time

from googleapiclient import discovery
from googleapiclient import errors as apierrors

#pylint: disable=no-member

class SlaveManager(object):
  """Class for managing Jenkins Slaves."""

  DEFAULT_SCOPES = ['https://www.googleapis.com/auth/devstorage.read_write']

  def __init__(self, project, zone=None):
    """Create a new SlaveManager.

    Args:
      project (str): the GCE project name.
      zone (str): the destination GCP zone.
    """
    self._project = project
    self._zone = zone

    self._client = self._CreateComputeClient()

  def _CreateComputeClient(self):
    """Creates an API client to do compute operations with.

    Returns:
      Resource: an object with methods for interacting with the service.
    """
    return discovery.build('compute', 'v1')

  def _WaitForOperation(self, operation):
    """Waits for an API operation to complete.

    Args:
      operation (dict): the API request.

    Returns:
      dict: the API call response.
    """
    while True:
      result = self._client.zoneOperations().get(
          project=self._project, zone=self._zone, operation=operation['name']
      ).execute()
      if result['status'] == 'DONE':
        if 'error' in result:
          raise Exception(result['error'])
        return result
      time.sleep(1)

  def _BuildPersistentDiskList(self, persistent_disks):
    """Builds a list of dicts describing all disks to attach.

    Args:
      persistent_disks (dict(str:str)]): list of disks to attach, in the form
        {'persistent_disk_name': 'device_name'}.

    Returns:
      list (dict): the list of disks to attach.
    """
    disk_list = list()
    mode = 'READ_ONLY'
    if persistent_disks:
      for disk_name, device in persistent_disks.items():
        source_url = (
            'https://www.googleapis.com/compute/v1/projects/{0:s}/zones/{1:s}/'
            'disks/{2:s}').format(self._project, self._zone, disk_name)
        disk_list.append(
            {
                'deviceName': device,
                'source': source_url,
                'mode': mode
            }
        )
    return disk_list

  def CreateInstance(
      self, instance_name, disk_size=None, source_image=None, machinetype=None,
      metadata=None, network=None, persistent_disks=None, scopes=None):
    """Creates a GCE instance.

    Args:
        instance_name (str): the name to give to the instance.
        disk_size (Optional[int]): the size of the system disk, in GB.
          Must be larger than the image size.
        source_image (Optional[str]): the path to the disk image to use.
          Must be in the form: '/projects/<project_name>/zones/images/...'])
        machinetype (Optional[str]): the type of the machine to use.
          For a list of valid values, see:
          https://cloud.google.com/compute/docs/machine-types
        metadata (Optional[dict]): optional metadata to set for the instance.
        network (Optional[str]): type of network to use (default: 'default')
        persistent_disks (Optional[dict(str:str)]): list of disks to attach to
          the instance, in the form {'persistent_disk_name': 'device_name'}.
        scopes (Optional[list[str]]): the list of scopes to set for the instance
    """
    scopes = scopes or self.DEFAULT_SCOPES

    print('Creating new instance {0:s}'.format(instance_name))

    project_url = 'compute/v1/projects/{0:s}'.format(self._project)
    machine_type_url = '{0:s}/zones/{1:s}/machineTypes/{2:s}'.format(
        project_url, self._zone, machinetype)
    network_url = '{0:s}/global/networks/{1:s}'.format(project_url, network)

    disks = [
        {
            'index': 0,
            'boot': True,
            'mode': 'READ_WRITE',
            'autoDelete': True,
            'initializeParams': {
                'diskName': '{0:s}-bootdisk'.format(instance_name),
                'diskSizeGb': disk_size,
                'sourceImage': source_image,
            }
        }
    ]

    persistent_disks = self._BuildPersistentDiskList(persistent_disks)
    for persistent_disk in persistent_disks:
      disks.append(persistent_disk)

    instance_dict = {
        'name': instance_name,
        'machineType': machine_type_url,
        'disks': disks,
        'networkInterfaces': [{
            'accessConfigs': [{
                'type': 'ONE_TO_ONE_NAT', 'name': 'External NAT'}],
            'network': network_url, }],
        'serviceAccounts': [{
            'email': 'default',
            'scopes': scopes,
        }],
    }
    if metadata:
      instance_dict['metadata'] = metadata

    operation = self._client.instances().insert(
        project=self._project, body=instance_dict, zone=self._zone).execute()
    self._WaitForOperation(operation)


def Main():
  """The main function.

  Returns:
    bool: True if successful or False otherwise.
  """
  parser = argparse.ArgumentParser()
  parser.add_argument(
      '--attach_persistent_disk', action='append', required=False,
      metavar=('PERSISTENT_DISK'), help=(
          'Attach PERSISTENT_DISK to the instance (ie: "evidence-images"). '
          'It will be attached as /dev/disk/by-id/google-PERSISTENT_DISK')
  )
  parser.add_argument(
      '--attach_persistent_disk_with_name', action='append', required=False,
      metavar=('PERSISTENT_DISK:DEVICE_NAME'), help=(
          'Attach PERSISTENT_DISK to the instance (ie: "evidence-images"). '
          'It will be attached as /dev/disk/by-id/google-DEVICE_NAME')
  )
  parser.add_argument(
      '--disk_size', action='store', required=False, default=200, type=int,
      help='Boot disk size, in GB (Default: %(default)s)')
  parser.add_argument(
      '--instance_name', action='store', required=True, help='Name of instance')
  parser.add_argument(
      '--source_image', action='store', required=True,
      help='Path to the image, ie: /projects/<project_name>/zones/images/...')
  parser.add_argument(
      '--linux_startup_script_url', action='store', required=False,
      metavar=('SCRIPT_URL'),
      help='GCS url to a startup script for a Linux instance')
  parser.add_argument(
      '--machine_type', action='store', required=False, default='n1-standard-8',
      help=('Type of machine (Default: "%(default)s)". For a list of valid '
            'values, see https://cloud.google.com/compute/docs/machine-types'))
  parser.add_argument(
      '--network', action='store', required=False, default='default',
      help='Type of network to use (Default: "%(default)s")')
  parser.add_argument(
      '--project', action='store', required=True, help='Name of the project')
  parser.add_argument(
      '--ssh_public_key', action='append', required=False,
      help=('Specify SSH public keys to use. '
            'Example: \'root:ssh-rsa AAAA... root\''))
  parser.add_argument(
      '--windows_startup_script_url', action='store', required=False,
      metavar=('SCRIPT_URL'),
      help='GCS url to a startup script for a Windows instance')
  parser.add_argument(
      '--zone', action='store', required=True, help='The zone for the instance')

  flags = parser.parse_args(sys.argv[1:])

  instance_metadata = None

  manager = SlaveManager(project=flags.project, zone=flags.zone)

  instance_metadata = {'items': []}

  if flags.windows_startup_script_url:
    startup_item = {
        'key': 'windows-startup-script-url',
        'value': flags.windows_startup_script_url
    }
    instance_metadata['items'].append(startup_item)

  if flags.linux_startup_script_url:
    startup_item = {
        'key': 'startup-script-url',
        'value': flags.linux_startup_script_url
    }
    instance_metadata['items'].append(startup_item)

  if flags.ssh_public_key:
    ssh_key_item = {
        'key': 'ssh-keys',
        'value': '\n'.join(flags.ssh_public_key)
    }
    instance_metadata['items'].append(ssh_key_item)

  persistent_disks_dict = {}

  pd_name = flags.attach_persistent_disk
  if pd_name:
    persistent_disks_dict[pd_name] = pd_name
  if flags.attach_persistent_disk_with_name:
    pd_name, device_name = flags.attach_persistent_disk_with_name.split(':')
    persistent_disks_dict[device_name] = pd_name

  try:
    manager.CreateInstance(
        flags.instance_name, persistent_disks=persistent_disks_dict,
        source_image=flags.source_image, machinetype=flags.machine_type,
        metadata=instance_metadata, network=flags.network)
  except apierrors.HttpError as error:
    error_dict = json.loads(error.content)
    status = error_dict['error'].get('code', None)
    error_message = error_dict['error'].get('message', '')
    if status == 409 and error_message.endswith('already exists'):
      print(error_message)
    if status == 400 and error_message.endswith(
        'The referenced image resource cannot be found.'):
      print(error_message)
    else:
      raise error

  return True


if __name__ == '__main__':
  if not Main():
    sys.exit(1)
  else:
    sys.exit(0)
