import unittest
from plaso.parsers.plist_plugins import ios_siminfo
from tests.parsers.plist_plugins import test_lib


class IOSSIMInfoPluginTest(test_lib.PlistPluginTestCase):
    """Test untuk plugin iOS SIM Info."""

    def testProcess(self):
        """Menguji proses parsing plist menggunakan plugin iOS SIM Info."""
        # Nama file plist yang akan diuji
        plist_name = 'com.apple.commcenter.data.plist'

        # Membuat instance dari plugin
        plugin = ios_siminfo.IOSSIMInfoPlugin()

        # Memproses file plist dengan plugin
        storage_writer = self._ParsePlistFileWithPlugin(plugin, [plist_name], plist_name)

        # Mengambil jumlah event_data yang diproses
        number_of_event_data = storage_writer.GetNumberOfAttributeContainers('event_data')

        # Memastikan jumlah event_data yang diproses sesuai
        self.assertEqual(number_of_event_data, 1)

        # Mengambil daftar event_data
        events = list(storage_writer.GetAttributeContainers('event_data'))

        # Memastikan bahwa data di event pertama sesuai dengan yang diharapkan
        event = events[0]
        self.assertEqual(event.mdn, '+19195794674')
        self.assertEqual(event.eap_aka, True)
        self.assertEqual(event.sim_type, 'sim')
        self.assertEqual(event.cb_ver, '49.0')
        self.assertEqual(event.label_id, 'E8B6082D-F391-46CB-9780-0AF46534D89F')
        self.assertEqual(event.timestamp.timestamp, 1684326382)

        # Memastikan timestamp diubah ke format yang benar
        self.assertEqual(event.timestamp.CopyToDateTimeString(), '2023-05-17 12:26:22')


if __name__ == '__main__':
    unittest.main()
