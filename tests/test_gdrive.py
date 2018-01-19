from __future__ import print_function
from datetime import datetime
import os
from django.core.exceptions import (
    ImproperlyConfigured, SuspiciousFileOperation,
)
from django.core.files.base import ContentFile, File
from django.test import TestCase
from django.utils.six import BytesIO
from oauth2client.service_account import ServiceAccountCredentials

from storages.backends import gdrive

try:
    from unittest import mock
except ImportError:  # Python 3.2 and below
    import mock

class GDriveTestCase(TestCase):
    def setUp(self):
        self._gdrive_p12_keyfile_path = os.environ.get("GDRIVE_P12_KEYFILE_PATH", None)
        self._gdrive_client_email = os.environ.get("GDRIVE_CLIENT_EMAIL", None)
        self.fake_credentials = False

        if not self._gdrive_p12_keyfile_path or not self._gdrive_client_email:
            self.fake_credentials = True
            self._gdrive_p12_keyfile_path = "/fake/path.p12"
            self._gdrive_client_email = "fakeuser@fakeproject-1234.iam.gserviceaccount.com"


    def _gdrive_storage_instance(self):
        storage = None
        with self.settings(GDRIVE_P12_KEYFILE_PATH=self._gdrive_p12_keyfile_path), self.settings(
                GDRIVE_CLIENT_EMAIL=self._gdrive_client_email):

            if self.fake_credentials:
                with mock.patch.object(gdrive.GoogleAuth, 'Authorize'), mock.patch(
                        'pydrive.auth.ServiceAccountCredentials'):

                    storage = gdrive.GDriveStorage()
            else:
                storage = gdrive.GDriveStorage()

        return storage

    def test_no_gdrive_settings(self):
        with self.assertRaises(ImproperlyConfigured):
            gdrive.GDriveStorage()

    def test_still_one_missing_setting(self):
        with self.assertRaises(ImproperlyConfigured), self.settings(GDRIVE_P12_KEYFILE_PATH=self._gdrive_p12_keyfile_path):
            gdrive.GDriveStorage()


    def test_create_google_auth_instance(self):
        storage = self._gdrive_storage_instance()
        self.assertIsNotNone(storage)

