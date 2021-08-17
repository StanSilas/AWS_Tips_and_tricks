import boto3
import botocore

PROFILE = "saml"
BUCKET_NAME = "my_bucket_name"
# aws --profile saml s3api delete-object --bucket my_bucket_name --key 'whatever/abc/a' --version 1234

session = boto3.Session(profile_name = PROFILE)
s3 = session.resource('s3')
bucket = s3.Bucket(BUCKET_NAME)

def main():
    bucket = s3.Bucket(BUCKET_NAME)
    versions = bucket.object_versions.filter(Prefix="whatever/")
    i=0

    for version in versions.all():
        if is_delete_marker(version):
             version.delete()
             with open("output_logs.txt", "a") as f:
             	print("\ndeleting delete marker", i,version)
             	print("\ndeleting delete marker", i,version,file=f)
             	i=i+1


def is_delete_marker(version):
    try:
        # note head() is faster than get()
        version.head()
        return False
    except botocore.exceptions.ClientError as e:
        if 'x-amz-delete-marker' in e.response['ResponseMetadata']['HTTPHeaders']:
            return True
        # an older version of the key but not a DeleteMarker
        elif '404' == e.response['Error']['Code']:
            return False


if __name__ == '__main__':
    main()
