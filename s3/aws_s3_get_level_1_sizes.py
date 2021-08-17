import boto3

PROFILE = "saml"
BUCKET = "my_bucket"

session = boto3.Session(profile_name = PROFILE)
s3 = session.resource('s3')
bucket = s3.Bucket(BUCKET)




# conn = boto3.client('s3')
conn = session.client('s3')

top_level_folders = dict()

for key in conn.list_objects_v2(Bucket='my_bucket')['Contents']:

    folder = key['Key'].split('/')[0]
    print("Key %s in folder %s. %d bytes" % (key['Key'], folder, key['Size']))

    if folder in top_level_folders:
        top_level_folders[folder] += key['Size']
    else:
        top_level_folders[folder] = key['Size']


for folder, size in top_level_folders.items():
    print("Folder: %s, size: %d" % (folder, size))
