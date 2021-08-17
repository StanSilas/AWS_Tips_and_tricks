import boto3

PROFILE = "saml"
BUCKET = "my_bucket"

session = boto3.Session(profile_name = PROFILE)
s3 = session.resource('s3')
bucket = s3.Bucket(BUCKET)

print("Deleting Verisons First \n\n")
bucket.object_versions.filter(Prefix="a/b/c"c.delete()
bucket.object_versions.filter(Prefix="data/").delete()

print("Deleting versions is complete\n\n")

print("Moving on to deletion of object \n\n")

bucket.objects.filter(Prefix="a/b/c/").delete()
print("Deletion of objects is complete")
print("Thank you")


