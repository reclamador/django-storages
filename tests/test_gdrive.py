from datetime import datetime

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
        pass

    def test_no_gdrive_settings(self):
        with self.assertRaises(ImproperlyConfigured):
            gdrive.GDriveStorage()

    def test_still_one_missing_setting(self):
        with self.assertRaises(ImproperlyConfigured), self.settings(GDRIVE_PKEY_FILE_PATH="/fake/path"):
            gdrive.GDriveStorage()

    @mock.patch.object(gdrive.GoogleAuth, 'Authorize')
    @mock.patch('pydrive.auth.ServiceAccountCredentials')
    def test_create_google_auth_instance(self, mock_ServiceAccountCredentials, mock_Authorize):
        with self.settings(GDRIVE_PKEY_FILE_PATH="/fake/path"), self.settings(GDRIVE_CLIENT_EMAIL="fake@developer.gserviceaccount.com"):
            gdrive.GDriveStorage()