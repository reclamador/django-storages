# Google Drive storage class for Django pluggable storage system.
# Author: Jorge Arevalo <jorge.arevalo@reclamador.es>
# License: BSD
#
# Usage:
#
# Add below to settings.py:
# GDRIVE_PKEY_FILE_PATH = '/path/to/private/key/file'
# GDRIVE_CLIENT_EMAIL = 'whatever@developer.gserviceaccount.com'

from __future__ import absolute_import

import os
import json
import tempfile
from contextlib import contextmanager

from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible
from pydrive.files import ApiRequestError

from storages.utils import setting

@contextmanager
def tempinput(data):
    """
    Context Manager to build a temporary file in disk to store yaml configuration
    Credits: https://stackoverflow.com/a/11892712/593722
    :param data: The raw data to write to disk
    :return:
    """
    temp = tempfile.NamedTemporaryFile(delete=False)
    temp.write(data)
    temp.close()
    try:
        yield temp.name
    finally:
        os.unlink(temp.name)

class GDriveStorageException(Exception):
    pass


class GDriveFile(File):
    #TODO: Implement?
    pass


@deconstructible
class GDriveStorage(Storage):
    """Google Drive Storage class for Django pluggable storage system."""

    def __init__(self, **kwargs):
        """
        Creates a service object that allows to target queries at a Google Service identified by the given parameters.
        Google Service is for Google Drive API v3: https://developers.google.com/drive/v3/web/about-sdk
        Check
        https://developers.google.com/api-client-library/python/auth/service-accounts
        :param kwargs: key-value store with additional parameters for Google Drive API calls. Valid keys are:
        supportsTeamDrives, acknowledgeAbuse
        For valid values check functions's parameters at
        https://developers.google.com/resources/api-libraries/documentation/drive/v3/python/latest/index.html
        :type kwargs: dict
        """
        # Get configuration parameters
        pkey_file_path = setting("GDRIVE_PKEY_FILE_PATH", strict=True) #local path to private key file in PKCS12 format
        client_email = setting("GDRIVE_CLIENT_EMAIL", strict=True) # the email associated with the service account

        create_delegated = kwargs.get("create_delegated", '')
        self._supports_team_drives = kwargs.get("supportsTeamDrives", None)
        self._acknowledge_abuse = kwargs.get("acknowledgeAbuse", None)

        # Build a temporary YAML file containing expected parameters for ServiceAuth in PyDrive lib
        yaml_content = "client_config_backend: service\n" \
                       "service_config:\n  " \
                       "client_user_email: {}\n  " \
                       "client_service_email: {}\n  " \
                       "client_pkcs12_file_path: {}\n".format(create_delegated, client_email, pkey_file_path)

        # Google Drive authentication using PyDrive
        with tempinput(yaml_content) as tempfilename:
            gauth = GoogleAuth(settings_file=tempfilename)
            gauth.ServiceAuth()

            # Create GoogleDrive instance with authenticated GoogleAuth instance.
            self.drive = GoogleDrive(gauth)

    def delete(self, name):
        # Build an GoogleDriveFile object with desired id
        gdrive_file = self.drive.CreateFile(metadata={'id': name})

        # Delete it
        gdrive_file.Delete(param={"supportsTeamDrives": self._supports_team_drives})

    def exists(self, name):
        # Build an GoogleDriveFile object with desired id
        gdrive_file = self.drive.CreateFile(metadata={'id': name})
        try:
            # Try to fetch its metadata
            _ = gdrive_file.FetchMetadata()
        except ApiRequestError as e:
            # Could not fetch metadata: assume the file does not exist or is not accessible
            return False
        else:
            return True

    def listdir(self, path):
        directories, files = [], []
        # TODO: Implement
        return directories, files

    def size(self, name):
        # Build an GoogleDriveFile object with desired id
        gdrive_file = self.drive.CreateFile(metadata={'id': name})
        response = gdrive_file.FetchMetadata(fields='size')
        gdrive_file_metadata = json.dumps(response)

        # Size property is only valid for binary files. Check
        # https://developers.google.com/drive/v3/reference/files#resource
        return gdrive_file_metadata.get("size", None)

        # TODO: In case of no binary files, download it and get size directly from os

    def modified_time(self, name):
        # Build an GoogleDriveFile object with desired id
        gdrive_file = self.drive.CreateFile(metadata={'id': name})
        response = gdrive_file.FetchMetadata(fields='modifiedDate')
        gdrive_file_metadata = json.dumps(response)
        return gdrive_file_metadata.get("modifiedDate", None)

    def accessed_time(self, name):
        # Build an GoogleDriveFile object with desired id
        gdrive_file = self.drive.CreateFile(metadata={'id': name})
        response = gdrive_file.FetchMetadata(fields='lastViewedByMeDate')
        gdrive_file_metadata = json.dumps(response)
        return gdrive_file_metadata.get("lastViewedByMeDate", None)

    def url(self, name):
        # Build an GoogleDriveFile object with desired id
        gdrive_file = self.drive.CreateFile(metadata={'id': name})
        response = gdrive_file.FetchMetadata(fields='webContentLink')
        gdrive_file_metadata = json.dumps(response)
        return gdrive_file_metadata.get("webContentLink", None)

    def _open(self, name, mode='rb'):
        #TODO: Implement
        pass

    def _save(self, name, content):
        # TODO: Implement
        pass

    def _chunked_upload(self, content, dest_path):
        # TODO: Implement
        pass