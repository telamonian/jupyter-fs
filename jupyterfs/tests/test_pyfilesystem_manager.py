# *****************************************************************************
#
# Copyright (c) 2019, the jupyter-fs authors.
#
# This file is part of the jupyter-fs library, distributed under the terms of
# the Apache License 2.0.  The full license can be found in the LICENSE file.
#

import boto3, botocore
from jupyterfs.pyfilesystem_manager import PyFilesystemContentsManager

test_bucket = 'test'
test_contents = 'foo/nbar/nbaz'
test_endpoint_url = 'http://127.0.0.1:9000'
test_fname = 'foo.txt'

_boto_kw = dict(
    config=botocore.client.Config(signature_version=botocore.UNSIGNED),
    endpoint_url=test_endpoint_url,
)


def _s3Resource():
    return boto3.resource('s3', **_boto_kw)


def _s3CreateBucket(bucket_name):
    s3Resource = _s3Resource()

    # check if bucket already exists
    bucket = s3Resource.Bucket(bucket_name)
    bucket_exists = True
    try:
        s3Resource.meta.client.head_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError as e:
        # If it was a 404 error, then the bucket does not exist.
        error_code = e.response['Error']['Code']
        if error_code == '404':
            bucket_exists = False

    if not bucket_exists:
        # create the bucket
        s3Resource.create_bucket(Bucket=bucket_name)


def _s3DeleteBucket(bucket_name):
    s3Resource = _s3Resource()

    # check if bucket already exists
    bucket = s3Resource.Bucket(bucket_name)
    bucket_exists = True
    try:
        s3Resource.meta.client.head_bucket(Bucket=bucket_name)
    except botocore.exceptions.ClientError as e:
        # If it was a 404 error, then the bucket does not exist.
        error_code = e.response['Error']['Code']
        if error_code == '404':
            bucket_exists = False

    if bucket_exists:
        # delete the bucket
        for key in bucket.objects.all():
            key.delete()
        bucket.delete()


def _s3ContentsManager():
    s3Uri = 's3://{bucket}?endpoint_url={endpoint_url}'.format(bucket=test_bucket, endpoint_url=test_endpoint_url)
    return PyFilesystemContentsManager.open_fs(s3Uri)


class TestPyFilesystemContentsManagerS3:
    @classmethod
    def setup_class(cls):
        _s3DeleteBucket(test_bucket)

    def setup_method(self, method):
        _s3CreateBucket(test_bucket)

    def teardown_method(self, method):
        _s3DeleteBucket(test_bucket)

    def test_write_s3_read_s3(self):
        s3CM = _s3ContentsManager()

        fpaths = [
            '' + test_fname,
            'root0/' + test_fname,
            'root1/leaf1/' + test_fname
        ]

        # set up dir structure
        s3CM._save_directory('root0', None)
        s3CM._save_directory('root1', None)
        s3CM._save_directory('root1/leaf1', None)

        # save to root and tips
        s3CM.save(test_contents, fpaths[0])
        s3CM.save(test_contents, fpaths[1])
        s3CM.save(test_contents, fpaths[2])

        # read and check
        assert test_contents == s3CM.get(fpaths[0])
        assert test_contents == s3CM.get(fpaths[1])
        assert test_contents == s3CM.get(fpaths[2])

    # @classmethod
    # def teardown_class(cls):
    #     pass
