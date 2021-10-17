# -*- coding: utf-8 -*-
"""Windows known folders helper."""


class WindowsKnownFoldersHelper(object):
  """Windows known folders helper."""

  # pylint: disable=line-too-long

  _PATH_PER_GUID = {
      '{008ca0b1-55b4-4c56-b8a8-4de4b299d3be}': '{%APPDATA%\\Microsoft\\Windows\\AccountPictures',
      '{00bcfc5a-ed94-4e48-96a1-3f6217f21990}': '{%LOCALAPPDATA%\\Microsoft\\Windows\\RoamingTiles',
      '{0139d44e-6afe-49f2-8690-3dafcae6ffb8}': '{%ALLUSERSPROFILE%\\Microsoft\\Windows\\Start Menu\\Programs',
      '{0482af6c-08f1-4c34-8c90-e17ec98b1e17}': '%PUBLIC%\\AccountPictures',
      '{054fae61-4dd8-4787-80b6-090220c4b700}': '{%LOCALAPPDATA%\\Microsoft\\Windows\\GameExplorer',
      '{0762d272-c50a-4bb0-a382-697dcd729b80}': '%SYSTEMDRIVE%\\Users',
      '{0d4c3db6-03a3-462f-a0e6-08924c41b5d4}': '{%LOCALAPPDATA%\\Microsoft\\Windows\\ConnectedSearch\\History',
      '{15ca69b3-30ee-49c1-ace1-6b5ec372afb5}': '{%PUBLIC%\\Music\\Sample Playlists',
      '{1777f761-68ad-4d8a-87bd-30b759fa33dd}': '%USERPROFILE%\\Favorites',
      '{18989b1d-99b5-455b-841c-ab7c74e4ddfc}': '%USERPROFILE%\\Videos',
      '{1a6fdba2-f42d-4358-a798-b74d745926c5}': '%PUBLIC%\\RecordedTV.library-ms',
      '{1ac14e77-02e7-4e5d-b744-2eb1ae5198b7}': '%WINDIR%\\System32',
      '{1b3ea5dc-b587-4786-b4ef-bd1dc332aeae}': '{%APPDATA%\\Microsoft\\Windows\\Libraries',
      '{2112ab0a-c86a-4ffe-a368-0de96e47012e}': '{%APPDATA%\\Microsoft\\Windows\\Libraries\\Music.library-ms',
      '{2400183a-6185-49fb-a2d8-4a392a602ba3}': '%PUBLIC%\\Videos',
      '{24d89e24-2f19-4534-9dde-6a6671fbb8fe}': '{%USERPROFILE%\\OneDrive\\Documents',
      '{2a00375e-224c-49de-b8d1-440df7ef3ddc}': '%WINDIR%\\resources\\%CODEPAGE%',
      '{2b0f765d-c0e9-4171-908e-08a611b84ff6}': '{%APPDATA%\\Microsoft\\Windows\\Cookies',
      '{2c36c0aa-5812-4b87-bfd0-4cd0dfb19b39}': '{%LOCALAPPDATA%\\Microsoft\\Windows Photo Gallery\\Original Images',
      '{3214fab5-9757-4298-bb61-92a9deaa44ff}': '%PUBLIC%\\Music',
      '{339719b5-8c47-4894-94c2-d8f77add44a6}': '{%USERPROFILE%\\OneDrive\\Pictures',
      '{33e28130-4e1e-4676-835a-98395c3bc3bb}': '%USERPROFILE%\\Pictures',
      '{352481e8-33be-4251-ba85-6007caedcf9d}': '{%LOCALAPPDATA%\\Microsoft\\Windows\\Temporary Internet Files',
      '{374de290-123f-4565-9164-39c4925e467b}': '%USERPROFILE%\\Downloads',
      '{3d644c9b-1fb8-4f30-9b45-f670235f79c0}': '%PUBLIC%\\Downloads',
      '{3eb685db-65f9-4cf6-a03a-e3ef65729f3d}': '%USERPROFILE%\\AppData\\Roaming',
      '{48daf80b-e6cf-4f4e-b800-0e69d84ee384}': '{%ALLUSERSPROFILE%\\Microsoft\\Windows\\Libraries',
      '{491e922f-5643-4af4-a7eb-4e7a138d8174}': '{%APPDATA%\\Microsoft\\Windows\\Libraries\\Videos.library-ms',
      '{4bd8d571-6d19-48d3-be97-422220080e43}': '%USERPROFILE%\\Music',
      '{4c5c32ff-bb9d-43b0-b5b4-2d72e54eaaa4}': '%USERPROFILE%\\Saved Games',
      '{52a4f021-7b75-48a9-9f6b-4b87a210bc8f}': '{%APPDATA%\\Microsoft\\Internet Explorer\\Quick Launch',
      '{5cd7aee2-2219-4a67-b85d-6c9ce15660cb}': '%LOCALAPPDATA%\\Programs',
      '{5ce4a5e9-e4eb-479d-b89f-130c02886155}': '{%ALLUSERSPROFILE%\\Microsoft\\Windows\\DeviceMetadataStore',
      '{5e6c858f-0e22-4760-9afe-ea3317b67173}': '{%SYSTEMDRIVE%\\Users\\%USERNAME%',
      '{625b53c3-ab48-4ec1-ba1f-a1ef4146fc19}': '{%APPDATA%\\Microsoft\\Windows\\Start Menu',
      '{62ab5d82-fdc1-4dc3-a9dd-070d1d495d97}': '%SYSTEMDRIVE%\\ProgramData',
      '{6365d5a7-0f0d-45e5-87f6-0da56b6a4f7d}': '%PROGRAMFILES%\\Common Files',
      '{69d2cf90-fc33-4fb7-9a0c-ebb0f0fcb43c}': '{%USERPROFILE%\\Pictures\\Slide Shows',
      '{6d809377-6af0-444b-8957-a3773f02200e}': '%SYSTEMDRIVE%\\Program Files',
      '{724ef170-a42d-4fef-9f26-b60e846fba4f}': '{%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\Administrative Tools',
      '{767e6811-49cb-4273-87c2-20f355e1085b}': '%USERPROFILE%\\OneDrive\\Pictures\\Camera Roll',
      '{7b0db17d-9cd2-4a93-9733-46cc89022e7c}': '%APPDATA%\\Microsoft\\Windows\\Libraries\\Documents.library-ms',
      '{7b396e54-9ec5-4300-be0a-2482ebae1a26}': '%PROGRAMFILES%\\Windows Sidebar\\Gadgets',
      '{7c5a40ef-a0fb-4bfc-874a-c0f2e0b9fa8e}': '%PROGRAMFILES% (%SYSTEMDRIVE%\\Program Files)',
      '{7d1d3a04-debb-4115-95cf-2f29da2920da}': '%USERPROFILE%\\Searches',
      '{7e636bfe-dfa9-4d5e-b456-d7b39851d8a9}': '%LOCALAPPDATA%\\Microsoft\\Windows\\ConnectedSearch\\Templates',
      '{82a5ea35-d9cd-47c5-9629-e15d2f714e6e}': '%ALLUSERSPROFILE%\\Microsoft\\Windows\\Start Menu\\Programs\\StartUp',
      '{859ead94-2e85-48ad-a71a-0969cb56a6cd}': '%PUBLIC%\\Videos\\Sample Videos',
      '{8983036c-27c0-404b-8f08-102d10dcfd74}': '%APPDATA%\\Microsoft\\Windows\\SendTo',
      '{8ad10c31-2adb-4296-a8f7-e4701232c972}': '%WINDIR%\\Resources',
      '{905e63b6-c1bf-494e-b29c-65b732d3d21a}': '%SYSTEMDRIVE%\\Program Files',
      '{9274bd8d-cfd1-41c3-b35e-b13f55a758f4}': '%APPDATA%\\Microsoft\\Windows\\Printer Shortcuts',
      '{9e3995ab-1f9c-4f13-b827-48b24b6c7174}': '%APPDATA%\\Microsoft\\Internet Explorer\\Quick Launch\\User Pinned',
      '{9e52ab10-f80d-49df-acb8-4330f5687855}': '%LOCALAPPDATA%\\Microsoft\\Windows\\Burn\\Burn',
      '{a3918781-e5f2-4890-b3d9-a7e54332328c}': '%LOCALAPPDATA%\\Microsoft\\Windows\\Application Shortcuts',
      '{a4115719-d62e-491d-aa7c-e74b8be3b067}': '%ALLUSERSPROFILE%\\Microsoft\\Windows\\Start Menu',
      '{a520a1a4-1780-4ff6-bd18-167343c5af16}': '%USERPROFILE%\\AppData\\LocalLow',
      '{a52bba46-e9e1-435f-b3d9-28daa648c0f6}': '%USERPROFILE%\\OneDrive',
      '{a63293e8-664e-48db-a079-df759e0509f7}': '%APPDATA%\\Microsoft\\Windows\\Templates',
      '{a75d362e-50fc-4fb7-ac2c-a8beaa314493}': '%LOCALAPPDATA%\\Microsoft\\Windows Sidebar\\Gadgets',
      '{a77f5d77-2e2b-44c3-a6a2-aba601054a51}': '%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs',
      '{a990ae9f-a03b-4e80-94bc-9912d7504104}': '%APPDATA%\\Microsoft\\Windows\\Libraries\\Pictures.library-ms',
      '{aaa8d5a5-f1d6-4259-baa8-78e7ef60835e}': '%LOCALAPPDATA%\\Microsoft\\Windows\\RoamedTileImages',
      '{ab5fb87b-7ce2-4f83-915d-550846c9537b}': '%USERPROFILE%\\Pictures\\Camera Roll',
      '{ae50c081-ebd2-438a-8655-8a092e34987a}': '%APPDATA%\\Microsoft\\Windows\\Recent',
      '{b250c668-f57d-4ee1-a63c-290ee7d1aa1f}': '%PUBLIC%\\Music\\Sample Music',
      '{b4bfcc3a-db2c-424c-b029-7fe99a87c641}': '%USERPROFILE%\\Desktop',
      '{b6ebfb86-6907-413c-9af7-4fc2abf07cc5}': '%PUBLIC%\\Pictures',
      '{b7bede81-df94-4682-a7d8-57a52620b86f}': '%USERPROFILE%\\Pictures\\Screenshots',
      '{b94237e7-57ac-4347-9151-b08c6c32d1f7}': '%ALLUSERSPROFILE%\\Microsoft\\Windows\\Templates',
      '{b97d20bb-f46a-4c97-ba10-5e3608430854}': '%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\StartUp',
      '{bcb5256f-79f6-4cee-b725-dc34e402fd46}': '%APPDATA%\\Microsoft\\Internet Explorer\\Quick Launch\\User Pinned\\ImplicitAppShortcuts',
      '{bcbd3057-ca5c-4622-b42d-bc56db0ae516}': '%LOCALAPPDATA%\\Programs\\Common',
      '{bfb9d5e0-c6a9-404c-b2b2-ae6db6af4968}': '%USERPROFILE%\\Links',
      '{c1bae2d0-10df-4334-bedd-7aa20b227a9d}': '%ALLUSERSPROFILE%\\OEM Links',
      '{c4900540-2379-4c75-844b-64e6faf8716b}': '%PUBLIC%\\Pictures\\Sample Pictures',
      '{c4aa340d-f20f-4863-afef-f87ef2e6ba25}': '%PUBLIC%\\Desktop',
      '{c5abbf53-e17f-4121-8900-86626fc2c973}': '%APPDATA%\\Microsoft\\Windows\\Network Shortcuts',
      '{c870044b-f49e-4126-a9c3-b52a1ff411e8}': '%LOCALAPPDATA%\\Microsoft\\Windows\\Ringtones',
      '{d0384e7d-bac3-4797-8f14-cba229b392b5}': '%ALLUSERSPROFILE%\\Microsoft\\Windows\\Start Menu\\Programs\\Administrative Tools',
      '{d65231b0-b2f1-4857-a4ce-a8e7c6ea7d27}': '%WINDIR%\\system32',
      '{d9dc8a3b-b784-432e-a781-5a1130a75963}': '%LOCALAPPDATA%\\Microsoft\\Windows\\History',
      '{de92c1c7-837f-4f69-a3bb-86e631204a23}': '%USERPROFILE%\\Music\\Playlists',
      '{de974d24-d9c6-4d3e-bf91-f4455120b917}': '%PROGRAMFILES%\\Common Files',
      '{debf2536-e1a8-4c59-b6a2-414586476aea}': '%ALLUSERSPROFILE%\\Microsoft\\Windows\\GameExplorer',
      '{dfdf76a2-c82a-4d63-906a-5644ac457385}': '%SYSTEMDRIVE%\\Users\\Public',
      '{e555ab60-153b-4d17-9f04-a5fe99fc15ec}': '%ALLUSERSPROFILE%\\Microsoft\\Windows\\Ringtones',
      '{ed4824af-dce4-45a8-81e2-fc7965083634}': '%PUBLIC%\\Documents',
      '{f1b32785-6fba-4fcf-9d55-7b8e7f157091}': '%USERPROFILE%\\AppData\\Local',
      '{f38bf404-1d43-42f2-9305-67de0b28fc23}': '%WINDIR%',
      '{f7f1ed05-9f6d-47a2-aaae-29d317c6f066}': '%PROGRAMFILES%\\Common Files',
      '{fd228cb7-ae11-4ae3-864c-16f3910ab8fe}': '%WINDIR%\\Fonts',
      '{fdd39ad0-238f-46af-adb4-6c85480369c7}': '%USERPROFILE%\\Documents'}

  # pylint: enable=line-too-long

  @classmethod
  def GetPath(cls, known_folder_identifier):
    """Retrieves the path for a specific known folder identifier.

    Args:
      known_folder_identifier (str): known folder identifier in the format
          "{GUID}".

    Returns:
      str: path represented by the known folder identifier or None of not
          available.
    """
    return cls._PATH_PER_GUID.get(known_folder_identifier.lower(), None)
