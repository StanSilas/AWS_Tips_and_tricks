Dec 27 2023:  
The tutorial assumes at least three years of hands on experience with S3 and athena. 
As organizations dive deeper into the world of S3 from a GRC standpoint, attribution of the who what where when and why becomes ultra important. While AWS does not provide something like this intuitively, using a combination of Athena S3  
server access logging can help us understand these key elements. 


Step 1  enable S3 server access logging. See existing documentation on how to do this.     
Step 2 enable cloudtrail logging. See existing documentation on how to do this.   
Step 3 create new tables on top of these two buckets so the created buckets carry logs in a tabular format.   
Step 4 Setup partitions to go around AWS's query limits and to query specific columns fast. Yes it's crazy but S3 gets limited by Athena very often.    
Step 5 Query these tables to understand what's happening with your buckets. 

Create Athena Tables:  
```
CREATE EXTERNAL TABLE `mybucket_logss`(
  `bucketowner` string COMMENT '', 
  `bucket_name` string COMMENT '', 
  `requestdatetime` string COMMENT '', 
  `remoteip` string COMMENT '', 
  `requester` string COMMENT '', 
  `requestid` string COMMENT '', 
  `operation` string COMMENT '', 
  `key` string COMMENT '', 
  `request_uri` string COMMENT '', 
  `httpstatus` string COMMENT '', 
  `errorcode` string COMMENT '', 
  `bytessent` bigint COMMENT '', 
  `objectsize` bigint COMMENT '', 
  `totaltime` string COMMENT '', 
  `turnaroundtime` string COMMENT '', 
  `referrer` string COMMENT '', 
  `useragent` string COMMENT '', 
  `versionid` string COMMENT '', 
  `hostid` string COMMENT '', 
  `sigv` string COMMENT '', 
  `ciphersuite` string COMMENT '', 
  `authtype` string COMMENT '', 
  `endpoint` string COMMENT '', 
  `tlsversion` string COMMENT '')
ROW FORMAT SERDE 
  'org.apache.hadoop.hive.serde2.RegexSerDe' 
WITH SERDEPROPERTIES ( 
  'input.regex'='([^ ]*) ([^ ]*) \\[(.*?)\\] ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) (\"[^\"]*\"|-) (-|[0-9]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) (\"[^\"]*\"|-) ([^ ]*)(?: ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*) ([^ ]*))?.*$') 
STORED AS INPUTFORMAT 
  'org.apache.hadoop.mapred.TextInputFormat' 
OUTPUTFORMAT 
  'org.apache.hadoop.hive.ql.io.HiveIgnoreKeyTextOutputFormat'
LOCATION
  's3://yourS3Bucket/S3/my-cloudtrail-logs/'
TBLPROPERTIES (
  'transient_lastDdlTime'='1683843508')

``` 


Understand what's in your table: 
SELECT * FROM "cloudtrail-csv"."mybucket_logss" limit 10;  

```
bucketowner
string

bucket_name
string

requestdatetime
string

remoteip
string

requester
string

requestid
string

operation
string

key
string

request_uri
string

httpstatus
string

errorcode
string

bytessent
bigint

objectsize
bigint

totaltime
string

turnaroundtime
string

referrer
string

useragent
string

versionid
string

hostid
string

sigv
string

ciphersuite
string

authtype
string

endpoint
string

tlsversion
string


```

Understand operations and requesters:  

```
SELECT count(*), operation, requester
FROM "mybucket_logss"
where bucket_name='shipt-cloudtrail-logs' AND requestdatetime > '01/Apr/2023' AND requestdatetime < '01/May/2023'
group by operation, requester
limit 100;
```

Add partitions on columns you are wanting to explore better and faster, in this case the date:  
```
ALTER TABLE cloudtrail_logs2 ADD 
   PARTITION (region='us-east-1',
              year='2023',
              month='07',
              day='06')
   LOCATION 's3://bucketname/AWSLogs/accountnumber/CloudTrail/us-east-1/2023/07/06/'
```

Understand User identity 
```

SELECT useridentity,eventname,sourceipaddress  FROM "cloudtrail-csv"."cloudtrail_logs2" where
              year='2023' and
              month='05'  and
              eventsource = 's3.amazonaws.com' AND               json_extract_scalar(requestparameters, '$.bucketName') = 'bucket_of_interest' limit 2000;
```


Understand what requester is making how many operations:  

```
SELECT count(*), operation, requester
FROM "mybucket_logss"
where bucket_name='your-cloudtrail-logs' AND requestdatetime > '01/Apr/2023' AND requestdatetime < '01/May/2023'
group by operation, requester
limit 100;
```

For more expert tutorials visit vivekmangipudi.wordpress.com   
