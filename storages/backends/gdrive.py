# Google Drive storage class for Django pluggable storage system.
# Author: Jorge Arevalo <jorge.arevalo@reclamador.es>
# License: BSD
#
# Usage:
#
# Add below to settings.py:
# GDRIVE_PKEY_FILE_PATH = '/path/to/private/key/file'
# GDRIVE_PKEY_PASSWORD = 'notasecret'
# GDRIVE_CLIENT_EMAIL = 'whatever@developer.gserviceaccount.com'

from __future__ import absolute_import

from datetime import datetime
from shutil import copyfileobj
from tempfile import SpooledTemporaryFile
import os
import json
from mimetypes import MimeTypes

from apiclient import discovery
from googleapiclient.errors import HttpError
from oauth2client.service_account import ServiceAccountCredentials

import httplib2


from django.core.exceptions import ImproperlyConfigured
from django.core.files.base import File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

from storages.utils import setting

VALID_MIME_TYPES_FOR_PKEY_FILE_DICT = {
    "PKCS12": 'application/x-pkcs12',
    "JSON": 'application/json'
}
VALID_EXTENSIONS_FOR_PKEY_FILE_DICT = {
    "PKCS12": '.pkcs12',
    "JSON": '.json'
}
SCOPES = ['https://www.googleapis.com/auth/drive']


class GDriveStorageException(Exception):
    pass


class GDriveFile(File):
    #TODO: Implement?
    pass


@deconstructible
class GDriveStorage(Storage):
    """Google Drive Storage class for Django pluggable storage system."""

    CHUNK_SIZE = 4 * 1024 * 1024

    def _build_credentials_object(self, pkey_file_path, client_email=None, private_key_password=None):
        """
        Buils a credentials object to authenticate with Google
        :param pkey_file_path: local path to private key file in PKCS12 or JSON format
        :param client_email: the email associated with the service account
        :param private_key_password: password associated with the private key (if the password exists)
        :return: Service Account credential for OAuth 2.0 signed JWT grants
        """
        mime = MimeTypes()

        # Try to get mime type
        (mimetype, _) = mime.guess_type(pkey_file_path)

        # Not valid mimetype. Try with file extension
        if not mimetype or mimetype.lower() not in VALID_MIME_TYPES_FOR_PKEY_FILE_DICT.values():
            _, file_extension = os.path.splitext(pkey_file_path)

            if file_extension.lower() not in VALID_EXTENSIONS_FOR_PKEY_FILE_DICT.values():
                raise ImproperlyConfigured("You must provide a valid PKCS12 / JSON private key file")

            elif file_extension.lower() == VALID_EXTENSIONS_FOR_PKEY_FILE_DICT["PKCS12"]:
                mimetype = VALID_MIME_TYPES_FOR_PKEY_FILE_DICT["PKCS12"]

            else:
                mimetype = VALID_MIME_TYPES_FOR_PKEY_FILE_DICT["JSON"]

        # File in PKCS12 format
        if mimetype == VALID_MIME_TYPES_FOR_PKEY_FILE_DICT["PKCS12"]:
            return ServiceAccountCredentials.from_p12_keyfile(client_email, pkey_file_path, private_key_password,
                                                              SCOPES)

        # File in JSON format
        else:
            return ServiceAccountCredentials.from_json_keyfile_name(pkey_file_path, SCOPES)

    def __init__(self, **kwargs):
        """
        Creates a service object that allows to target queries at a Google Service identified by the given parameters.
        Google Service is for Google Drive API v3: https://developers.google.com/drive/v3/web/about-sdk
        Check
        https://developers.google.com/api-client-library/python/auth/service-accounts
        :param kwargs: optional config values. Accepted keys:
            * create_delegated: string, email of an existent user, in case we delegated domain-wide access to the
            service account and want to impersonate a user account
            * supportsTeamDrives: boolean, whether the requesting application supports Team Drives
            * acknowledgeAbuse: boolean, Whether the user is acknowledging the risk of downloading known malware or
            other abusive files.
        """
        # Get configuration parameters
        pkey_file_path = setting("GDRIVE_PKEY_FILE_PATH", None) #local path to private key file in PKCS12 or JSON format
        client_email = setting("GDRIVE_CLIENT_EMAIL", None) # the email associated with the service account
        private_key_password = setting("GDRIVE_PKEY_PASSWORD",
                                       None) # password associated with the private key (if the password exists)

        delegated_email = kwargs.get("create_delegated", None)
        support_team_drives = kwargs.get("supportsTeamDrives", None)
        acknowledge_abuse = kwargs.get("acknowledgeAbuse", None)


        # Build credentials to Google Service account auth
        credentials = self._build_credentials_object(pkey_file_path, client_email, private_key_password)

        # If we want to impersonate another user
        if delegated_email is not None:
            credentials = credentials.create_delegated(delegated_email)

        # Build the service object
        http = credentials.authorize(httplib2.Http())
        self.client = discovery.build('drive', 'v3', http=http)

        # Store config parameter
        self._support_team_drives = support_team_drives
        self._acknowledge_abuse = acknowledge_abuse

    def delete(self, name):
        self.client.files().delete(fileId=name, supportTeamDrives=self._support_team_drives)

    def exists(self, name):
        try:
            _ = self.client.files().get(fileId=name, acknowledgeAbuse=self._acknowledge_abuse)
        except HttpError as e:
            return False
        else:
            return True

    def listdir(self, path):
        directories, files = [], []
        # TODO: Implement
        return directories, files

    def size(self, name):
        response = self.client.files().get(fileId=name, acknowledgeAbuse=self._acknowledge_abuse, fields='size')
        gdrive_file_metadata = json.dumps(response)

        # Size property is only valid for binary files. Check
        # https://developers.google.com/drive/v3/reference/files#resource
        return gdrive_file_metadata.get("size", None)

        # TODO: In case of no binary files, download it and get size directly from os

    def modified_time(self, name):
        response = self.client.files().get(fileId=name, acknowledgeAbuse=self._acknowledge_abuse, fields='modifiedTime')
        gdrive_file_metadata = json.dumps(response)
        return gdrive_file_metadata.get("modifiedTime", None)

    def accessed_time(self, name):
        response = self.client.files().get(fileId=name, acknowledgeAbuse=self._acknowledge_abuse,
                                           fields='viewedByMeTime')
        gdrive_file_metadata = json.dumps(response)
        return gdrive_file_metadata.get("viewedByMeTime", None)

    def url(self, name):
        response = self.client.files().get(fileId=name, acknowledgeAbuse=self._acknowledge_abuse,
                                           fields='webContentLink')
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