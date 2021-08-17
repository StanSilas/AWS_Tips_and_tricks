import boto3

PROFILE = "saml"
BUCKET = "my_bucket"
Prefix="a/b/c"
Prefix="pan/"


session = boto3.Session(profile_name = PROFILE)
s3 = session.resource('s3')
bucket = s3.Bucket(BUCKET)

version = bucket.object_versions.filter(Prefix=Prefix)

for ver in version.all():
    if str(ver.size) in 'None':
        delete_file = ver.delete()
        print("\n",delete_file)
    else:
        delete_file = ver.delete()
        print("FILE DELETED\n",delete_file)
        pass
