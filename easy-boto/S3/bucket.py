import boto3
from botocore.exceptions import ClientError
import os
from typing import Union, Dict
from . import exceptions


class Bucket():
    """
    CLASS THAT HANDLES S3 BUCKET TRANSACTIONS. ABSTRACTS AWAY BOTO3'S ARCANE BULLSHIT.
    HANDLES BOTO3'S BULLSHIT EXCEPTIONS WITH CUSTOM EXCEPTION CLASSES TO MAKE CODE USABLE
    """

    def __init__(self, bucket_name: str):

        self.bucket_name = bucket_name

    @staticmethod
    def _get_boto3_resource():
        """
        GET AND CONFIGURE THE BOTO3 S3 API RESOURCE. THIS IS A "PRIVATE" METHOD
        """
        # CREATE A "SESSION" WITH BOTO3
        _session = boto3.Session(
            aws_access_key_id=os.environ.get("AWS_ACCESS_KEY"),
            aws_secret_access_key=os.environ.get("AWS_SECRET_KEY")
        )

        # CREATE S3 RESOURCE
        resource = _session.resource('s3')

        return resource

    def _handle_boto3_client_error(self, e: ClientError, key=None):

        """
        HANDLE BOTO3'S CLIENT ERROR. BOTO3 ONLY RETURNS ONE TYPE OF EXCEPTION, WITH DIFFERENT KEYS AND MESSAGES FOR
            DIFFERENT TYPES OF ERRORS. REFER TO EXCEPTIONS.PY FOR EXPLANATION

        :param e: THE CLIENTERROR TO HANDLE
        """
        error_code: str = e.response.get('Error').get('Code')

        print(e.response)

        if error_code == 'AccessDenied':
            raise exceptions.BucketAccessDenied(self.bucket_name)
        elif error_code == 'NoSuchBucket':
            raise exceptions.NoSuchBucket(self.bucket_name)
        elif error_code == 'NoSuchKey':
            raise exceptions.NoSuchKey(key, self.bucket_name)
        else:
            raise exceptions.UnknownBucketException(self.bucket_name, e)

    def get(self, key: str, responseContentType: str = None) -> (bytes, Dict):
        """
        GET AN OBJECT FROM THE BUCKET AND RETURN A BYTES TYPE THAT MUST BE DECODED ACCORDING TO THE ENCODING TYPE

        :param key: THE KEY IN S3 OF THE OBJECT TO GET
        :param responseContentType: THE CONTENT TYPE TO ENFORCE ON THE RESPONSE. MAY BE USEFUL IN SOME CASES
        :return: A TWO-TUPLE: (1) A BYTES OBJECT THAT MUST BE DECODED DEPENDING ON HOW IT WAS ENCODED.
            LEFT UP TO MIDDLEWARE TO DETERMINE AND (2) A DICT CONTAINING METADATA ON WHEN THE OBJECT WAS STORED
        """
        # GET S3 resource
        resource = Bucket._get_boto3_resource()
        s3_bucket = resource.Object(self.bucket_name, key)

        try:
            if responseContentType:
                response = s3_bucket.get(ResponseContentType=responseContentType)
            else:
                response = s3_bucket.get()

            data = response.get('Body').read()  # THE OBJECT DATA STORED
            metadata: Dict = response.get('Metadata')  # METADATA STORED WITH THE OBJECT
            return data, metadata

        # BOTO RAISES ONLY ONE ERROR TYPE THAT THEN MUST BE PROCESSES TO GET THE CODE
        except ClientError as e:
            self._handle_boto3_client_error(e, key=key)

    def put(self, key: str, data: Union[str, bytes], contentType: str = None, metadata: Dict = {}) -> Dict:
        """
        PUT AN OBJECT INTO THE BUCKET

        :param key: THE KEY TO STORE THE OBJECT UNDER
        :param data: THE DATA TO STORE. CAN BE BYTES OR STRING
        :param contentType: THE MIME TYPE TO STORE THE DATA AS. MAY BE IMPORTANT FOR BINARY DATA
        :param metadata: A DICT CONTAINING METADATA TO STORE WITH THE OBJECT. EXAMPLES INCLUDE TIMESTAMP OR
            ORGANIZATION NAME. VALUES _MUST_ BE STRINGS.
        :return: A DICT CONTAINING THE RESPONSE FROM S3. IF AN EXCEPTION IS NOT THROWN, ASSUME PUT OPERATION WAS SUCCESSFUL.
        """
        # GET RESOURCE
        resource = Bucket._get_boto3_resource()
        s3_bucket = resource.Object(self.bucket_name, key)

        # PUT IT
        try:
            if contentType:
                response = s3_bucket.put(
                    Body=data,
                    ContentType=contentType,
                    Key=key,
                    Metadata=metadata
                )
            else:
                response = s3_bucket.put(
                    Body=data,
                    Key=key,
                    Metadata=metadata
                )
            return response

        # BOTO RAISES ONLY ONE ERROR TYPE THAT THEN MUST BE PROCESSES TO GET THE CODE
        except ClientError as e:
            self._handle_boto3_client_error(e, key=key)

    def delete(self, key: str) -> Dict:
        """
        DELETE A SPECIFIED OBJECT FROM THE BUCKET

        :param key: A STRING THAT IS THE OBJECT'S KEY IDENTIFIER IN S3
        :return: THE RESPONSE FROM S3. IF NO EXCEPTION WAS THROWN, ASSUME DELETE OPERATION WAS SUCCESSFUL
        """
        # GET S3 RESOURCE
        resource = Bucket._get_boto3_resource()
        s3_bucket = resource.Object(self.bucket_name, key)

        try:
            response = s3_bucket.delete()
            return response

        # BOTO RAISES ONLY ONE ERROR TYPE THAT THEN MUST BE PROCESSES TO GET THE CODE
        except ClientError as e:
            self._handle_boto3_client_error(e, key=key)

    def upload_file(self, local_filepath: str, key: str) -> Dict:
        """
        UPLOAD A LOCAL FILE TO THE BUCKET. TRANSPARENTLY MANAGES MULTIPART UPLOADS.

        :param local_filepath: THE ABSOLUTE FILEPATH OF THE FILE TO STORE
        :param key: THE KEY TO STORE THE FILE UNDER IN THE BUCKET
        :return: A DICT CONTAINING THE RESPONSE FROM S3. IF NO EXCEPTION IS THROWN, ASSUME OPERATION
            COMPLETED SUCCESSFULLY
        """

        # GET S3 RESOURCE
        resource = Bucket._get_boto3_resource()
        s3_bucket = resource.Object(self.bucket_name, key)

        try:
            response = s3_bucket.upload_file(local_filepath)
            return response

            # BOTO RAISES ONLY ONE ERROR TYPE THAT THEN MUST BE PROCESSES TO GET THE CODE
        except ClientError as e:
            self._handle_boto3_client_error(e, key=key)

    def download_file(self, key: str, local_filepath: str) -> Dict:
        """
        DOWNLOAD AN OBJECT FROM THE BUCKET TO A LOCAL FILE. TRANSPARENTLY MANAGES MULTIPART DOWNLOADS.

        :param key: THE KEY THAT IDENTIFIES THE OBJECT TO DOWNLOAD
        :param local_filepath: THE ABSOLUTE FILEPATH TO STORE THE OBJECT TO
        :return: A DICT CONTAINING THE RESPONSE FROM S3. IF NO EXCEPTION IS THROWN, ASSUME OPERATION
            COMPLETED SUCCESSFULLY
        """
        # GET S3 RESOURCE
        resource = Bucket._get_boto3_resource()
        s3_bucket = resource.Object(self.bucket_name, key)

        try:
            response = s3_bucket.download_file(local_filepath)
            return response

            # BOTO RAISES ONLY ONE ERROR TYPE THAT THEN MUST BE PROCESSES TO GET THE CODE
        except ClientError as e:
            self._handle_boto3_client_error(e, key=key)