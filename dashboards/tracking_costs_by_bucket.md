So S3 is costing you 100,000 USD per month but you have no clue how to track down costs and attribute them to the buckets ?  
AWS Cost allocation tags come to your rescue!! 

AWS does cover this in their knowledge base: https://aws.amazon.com/premiumsupport/knowledge-center/s3-find-bucket-cost/. 

In short one needs to add a tag to every bucket and set the value to be the bucket name. 
Then you can use the cost explorer to find that total cost per bucket:
![image](https://user-images.githubusercontent.com/10617538/195479448-02ec2d70-1cef-4129-a8e0-32c37c88e207.png). 

If you have lots of buckets, this is very tedious and error-prone so how about an ugly python script ? :  
This will recurse through your buckets and append a new tag called s3-bucket-name and set the value to be that name of that bucket.

```
import boto3
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')
s3_resource = boto3.resource('s3')

def add_bucket_name_tag_to_all_buckets():
    TAG_NAME = 's3-bucket-name'

    for s3_bucket in s3_resource.buckets.all():
        s3_bucket_name = s3_bucket.name
        print(f'Setting tag "{TAG_NAME}" in "{s3_bucket_name}" to "{s3_bucket_name}"...')

        # Create tag iff there are no tags at all
        bucket_tagging = s3_resource.BucketTagging(s3_bucket_name)
        try:
            tags = bucket_tagging.tag_set # This throws if there are no tags
        except ClientError:
            tags = [{'Key':TAG_NAME, 'Value': s3_bucket_name}]
            bucket_tagging.put(Tagging={'TagSet':tags}) # Use carefully, this overwrites all tags

        # Now append tag if not present
        tags = bucket_tagging.tag_set
        if len([x for x in tags if x['Key'] == TAG_NAME]) == 0: # If tag not found, append it
            tags.append({'Key':TAG_NAME, 'Value': s3_bucket_name})
            bucket_tagging.put(Tagging={'TagSet':tags}) # Use carefully, this overwrites all tags


if __name__ == '__main__':
  add_bucket_name_tag_to_all_buckets()

```


To check which Amazon S3 bucket is increasing your storage cost, perform the following steps:

Add a common tag to each bucket.

Activate the tag as a cost allocation tag.

Important: All tags can take up to 24 hours to appear in the Billing and Cost Management console.

Use the AWS Cost Explorer to create an AWS Cost and Usage Report for your tag.
Note: Cost allocation tags don't show you costs that you incurred before you set up the tags.

Resolution Before you begin, your AWS Identity and Access Management (IAM) policy must have permissions to do the following:

Access the Billing and Cost Management console Perform the actions s3:GetBucketTagging and s3:PutBucketTagging Tip: Avoid using your AWS account root user for this solution. Instead, use an IAM user or role with the permissions that you need.

Adding a common tag to each bucket

Open the Amazon S3 console.

From the list of buckets, choose the bucket that you want to track costs for.

Choose the Properties view.

Scroll down and choose Tags.

Choose Edit.

Choose Add Tag.

For Key, enter a name for the tag that you'll add to all the buckets that you want to track costs for. For example, enter "S3-Bucket-Name".

For Value, enter the name of the bucket.

Repeat Steps 1 through 7 for all the buckets that you want to track costs.

Activating the tag as a cost allocation tag

Open the Billing and Cost Management console.

From the navigation pane, choose Cost allocation tags.

In the search bar, enter the name of the tag that you created for your buckets. For example, type "S3-Bucket-Name".

Select the tag.

Choose Activate.

Use the AWS Cost Explorer to create a cost report for the tag

Open the Billing and Cost Management console.

From the navigation pane, choose Cost Explorer.

Choose Launch Cost Explorer.

From the navigation pane, choose Reports.

Choose New report.

For Report Templates, select Cost & Usage report, and then choose Create Report.

Under Filters, for Service, select S3 (Simple Storage Service). Then, choose Apply filters.

For Tag, select the tag that you created. For example, select S3-Bucket-Name. Then, check each bucket that you want to track costs on, and choose Apply filters.

Note: If you don't see your tag in the filter list, it's likely that the tag was recently created and applied to a bucket. Wait 24 hours, and then try creating the report again.

Under Advanced options, confirm that Show only untagged resources is unchecked.

From the top of the graph, choose Group by, and then select the tag that you created.

Choose Save as.

Enter a title for your cost report.

Choose Save Report.

After you create the cost report, use the report to review the cost of each bucket marked with the cost allocation tag that you created.

Note: You can set up a daily or hourly AWS Cost and Usage Report report to get more Amazon S3 billing details. However, these reports don't show you who made requests to your buckets. To see where requests to your bucket are coming from, enable either object-level logging or server access logging. To get more information on certain Amazon S3 billing items, you must enable logging ahead of time. Then, you'll have logs that contain Amazon S3 request details.
