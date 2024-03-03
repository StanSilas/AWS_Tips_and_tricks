The storage lens dashboard is a fantastic start to understanding a TOP 25 in the world of S3. However by employing the following techniques, one can easily dive really far and deep into the S3 world to understand everything about every bucket
from a storage perspective. 


To first get a list of all buckets start with the fullowing S3 script
```
#!/bin/zsh
# list all s3 buckets

echo "start"

profiles=(
    "what-ever-is-your-account-name" 
   
)
target_file=$(echo $(date +'%Y-%m-%d')-buckets.csv)
touch $target_file

echo "no,bucket,env" >> $target_file

i=1
for value in $profiles
do
   echo "processing proejct $value ..."
   # set env variables
   eval $(aws-okta env $value)
   # get buckets
   buckets=( $(aws s3 ls | awk '{print $3}') )
   
   for bucket in $buckets
   do
      echo "$i,$bucket,$value" >> $target_file
      ((i=i+1))
   done
done





echo "end"
