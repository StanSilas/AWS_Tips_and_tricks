The storage lens dashboard is a fantastic start to understanding a TOP 25 in the world of S3.   
However by employing the following techniques, one can easily dive really far and deep into the S3 world to understand everything about every bucket
from a storage perspective. 


To first get a list of all buckets start with the following S3 script
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
```  



On AWS S3 lens dashboard, setup exporting of the S3 stats to an S3 bucket of your choice ex S3reporting. 
On IAM Dashboard setup IAM Access Keys and Secrets.  
You can use the following go code to analzye the created report daily.  
This is a very scalable solution that can be applied across unlimited numner of AWS accounts.   
This will help one gain full control over the nature of the S3 data.  


main.go  

```
/*
query report data from the S3 bucket S3reporting
and display some metrics
*/
package main

import (
	"bufio"
	"errors"
	"fmt"
	"io"
	"log"
	"os"
	"path/filepath"
	"strconv"
	"strings"
	"time"

	"github.com/StanSilas/report-s3/aws"
)

// report yesterday (today report is still in progress)
var yesterday string

func init() {
	yesterday = time.Now().Add(-24 * time.Hour).Format("2006-01-02")
	//yesterday = "2023-05-28"
}

func main() {
	log.Println("🌵 start")
	if os.Getenv("AWS_ACCESS_KEY_ID") == "" ||
		os.Getenv("AWS_SECRET_ACCESS_KEY") == "" {
		log.Fatalf(`🚩ERROR evn:
AWS_ACCESS_KEY_ID: %s
AWS_SECRET_ACCESS_KEY: %s`,
			os.Getenv("AWS_ACCESS_KEY_ID"),
			os.Getenv("AWS_SECRET_ACCESS_KEY"))
	}
	
	if err := touchFiles(); err != nil {
		log.Fatalln("🚩", err)
	}

	if err := report(); err != nil {
		log.Fatalln("🚩", err)
	}

	// show/save reports
	report, err := aws.ReportListLikeBucket([]string{""}, yesterday)
	// report, err := aws.Report(yesterday)
	// report, err := aws.ReportLikeBucket([]string{"abcd0", "abcd", "abcd1", "abcd3"}, yesterday)
	// report, err := aws.ReportLikeBucket([]string{""}, yesterday)
	if err != nil {
		log.Fatalln("🚩", err)
	}
	fmt.Println(report)
	saveCsvReport(report)

	log.Println("🌵 success")
}

// create all the necessary files for the report
func touchFiles() error {
	// touch dir
	_, err := os.Stat(yesterday)
	if err != nil {
		if errors.Is(err, os.ErrNotExist) {
			newpath := filepath.Join(".", yesterday)
			err = os.MkdirAll(newpath, os.ModePerm)
		}
	}
	if err != nil {
		return err
	}

	// check if already present
	for _, p := range aws.Profiles {
		file := fmt.Sprintf("%s/%s.csv", yesterday, p.Name)
		_, err := os.Stat(file)
		if err == nil {
			continue // file already present
		}
		rUrl, err := aws.GetRemoteURL(p.AccNumber, yesterday)
		if err != nil {
			return err
		}
		err = aws.DownloadRemoteFile(file, rUrl)
		if err != nil {
			return err
		}
		fmt.Println(file, "created")
	}

	return nil
}

func report() error {
	// filter report rows
	metric_name := map[string]bool{
		"StorageBytes":                            true,
		"CurrentVersionStorageBytes":              true,
		"NonCurrentVersionStorageBytes":           true,
		"DeleteMarkerStorageBytes":                true,
		"IncompleteMPUStorageBytesOlderThan7Days": true,
		"ObjectCount":                             true,
	}

	for _, p := range aws.Profiles {
		content, err := os.Open(fmt.Sprintf("%s/%s.csv", yesterday, p.Name))
		if err != nil {
			return err
		}
		defer content.Close()

		fileScanner := bufio.NewScanner(content)
		fileScanner.Split(bufio.ScanLines)
		for fileScanner.Scan() {
			line := strings.ReplaceAll(fileScanner.Text(), "\"", "")
			lt := strings.Split(line, ",")
			if len(lt) != 11 {
				return fmt.Errorf("invalid record %#v", lt)
			}
			/*
				 6: record_type {ACCOUNT | BUCKET | PREFIX}
				 8: bucket_name
				 9: metric_name
					- StorageBytes
					- CurrentVersionStorageBytes
					- NonCurrentVersionStorageBytes
					- DeleteMarkerStorageBytes
					- IncompleteMPUStorageBytesOlderThan7Days
					- ObjectCount
				10: metric_value (on bytes)
			*/
			if !metric_name[lt[9]] {
				continue
			}

			size, err := strconv.ParseUint(lt[10], 10, 64)
			if err != nil {
				return fmt.Errorf("unexpected value %v", lt[10])
			}

			var stats *aws.Stats
			switch lt[6] { // ACCOUNT | BUCKET | PREFIX
			case "ACCOUNT":
				stats = &p.Stats
			case "BUCKET":
				b, ok := p.Buckets[lt[8]]
				if !ok {
					b = &aws.Bucket{
						Name:        lt[8],
						ProfileName: p.Name,
					}
					p.Buckets[lt[8]] = b
				}
				stats = &b.Stats
			default:
				// PREFIX, ignore
				continue
			}

			switch lt[9] {
			case "StorageBytes":
				stats.StorageBytes += size
			case "CurrentVersionStorageBytes":
				stats.CurrentVersionStorageBytes += size
			case "NonCurrentVersionStorageBytes":
				stats.NonCurrentVersionStorageBytes += size
			case "DeleteMarkerStorageBytes":
				stats.DeleteMarkerStorageBytes += size
			case "IncompleteMPUStorageBytesOlderThan7Days":
				stats.IncompleteMPUStorageBytesOlderThan7Days += size
			case "ObjectCount":
				stats.ObjectCount += size
			}
		}
	}

	return nil
}

func saveCsvReport(report string) error {
	f, err := os.Create(yesterday + "-report.csv")
	if err != nil {
		return err
	}

	_, err = io.WriteString(f, report)
	if closeErr := f.Close(); err == nil {
		err = closeErr
	}

	return err
}



echo "end"
```

aws.go   

```
package aws

import (
	"context"
	"fmt"
	"io"
	"os"
	"sort"
	"strings"

	"github.com/aws/aws-sdk-go-v2/aws"
	"github.com/aws/aws-sdk-go-v2/config"
	"github.com/aws/aws-sdk-go-v2/service/s3"
)

const (
	_             = 1 << (10 * iota)
	KiB           // 1024
	MiB           // 1048576
	GiB           // 1073741824
	TiB           // 1099511627776
	REPORT_BUCKET = "data-devops-s3-reporting"
	LIMIT         = 8
)

type Stats struct {
	StorageBytes                            uint64
	CurrentVersionStorageBytes              uint64
	NonCurrentVersionStorageBytes           uint64
	DeleteMarkerStorageBytes                uint64
	IncompleteMPUStorageBytesOlderThan7Days uint64
	ObjectCount                             uint64
}

type Bucket struct {
	Name        string
	ProfileName string
	Stats
}

type Profile struct {
	Name      string
	AccNumber string
	Buckets   map[string]*Bucket
	Stats
}

// AWS profiles to aggregate report data
var Profiles = []*Profile{
	{
		Name:      "Account1",
		AccNumber: "1234",
		Buckets:   map[string]*Bucket{},
	},
	{
		Name:      "Account10",
		AccNumber: "5678",
		Buckets:   map[string]*Bucket{},
	},
	{
		Name:      "AccountN",
		AccNumber: "9101112",
		Buckets:   map[string]*Bucket{},
	},
	
}

// the report-url given the environment and date
func GetRemoteURL(envNo, day string) (string, error) {
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		return "", err
	}
	client := s3.NewFromConfig(cfg)

	input := &s3.ListObjectsV2Input{
		Bucket: aws.String(REPORT_BUCKET),
		Prefix: aws.String("StorageLens/" +
			envNo +
			"/default-account-dashboard/V_1/reports/dt=" +
			day),
	}
	result, err := client.ListObjectsV2(context.TODO(), input)
	if err != nil {
		return "", err
	}

	if len(result.Contents) == 0 {
		return "", fmt.Errorf("there is NO DATA at %s", *input.Prefix)
	}

	sort.Slice(result.Contents, func(i, j int) bool {
		// put the bigger file first
		return result.Contents[i].Size > result.Contents[j].Size
	})

	return *result.Contents[0].Key, nil
}

// download the report to the given file
func DownloadRemoteFile(file, url string) error {
	cfg, err := config.LoadDefaultConfig(context.TODO())
	if err != nil {
		return err
	}

	client := s3.NewFromConfig(cfg)
	object := &s3.GetObjectInput{
		Bucket: aws.String(REPORT_BUCKET),
		Key:    aws.String(url),
	}
	result, err := client.GetObject(context.TODO(), object)
	if err != nil {
		return err
	}
	defer result.Body.Close()

	f, err := os.Create(file)
	if err != nil {
		return err
	}

	_, err = io.Copy(f, result.Body)
	if closeErr := f.Close(); err == nil {
		err = closeErr
	}

	return err
}

func (s Stats) String() string {
	return fmt.Sprintf(`
                           StorageBytes: %s
             CurrentVersionStorageBytes: %s
          NonCurrentVersionStorageBytes: %s
IncompleteMPUStorageBytesOlderThan7Days: %s
               DeleteMarkerStorageBytes: %s
                            ObjectCount: %d`,
		PrintBytes(s.StorageBytes),
		PrintBytes(s.CurrentVersionStorageBytes),
		PrintBytes(s.NonCurrentVersionStorageBytes),
		PrintBytes(s.IncompleteMPUStorageBytesOlderThan7Days),
		PrintBytes(s.DeleteMarkerStorageBytes),
		s.ObjectCount,
	)
}

func PrintBytes(b uint64) string {
	byte := float64(b)
	switch {
	case b > TiB:
		return fmt.Sprintf("%.2f TiB", byte/TiB)
	case b > GiB:
		return fmt.Sprintf("%.2f GiB", byte/GiB)
	case b > MiB:
		return fmt.Sprintf("%.2f MiB", byte/MiB)
	case b > KiB:
		return fmt.Sprintf("%.2f KiB", byte/KiB)
	default:
		return fmt.Sprintf("%d Bytes", b)
	}
}

func Report(day string) (string, error) {
	buckets := []Bucket{}
	stats := Stats{}

	// aggregate profiles and collect buckets
	for _, p := range Profiles {
		stats.StorageBytes += p.StorageBytes
		stats.CurrentVersionStorageBytes += p.CurrentVersionStorageBytes
		stats.NonCurrentVersionStorageBytes += p.NonCurrentVersionStorageBytes
		stats.IncompleteMPUStorageBytesOlderThan7Days += p.IncompleteMPUStorageBytesOlderThan7Days
		stats.DeleteMarkerStorageBytes += p.DeleteMarkerStorageBytes
		stats.ObjectCount += p.ObjectCount
		for _, b := range p.Buckets {
			buckets = append(buckets, *b)
		}
	}

	// sort to tget the top-10
	sort.Slice(buckets, func(i, j int) bool {
		return buckets[i].StorageBytes > buckets[j].StorageBytes
	})

	builder := strings.Builder{}
	_, err := builder.WriteString(fmt.Sprintf("S3 %s\n", day))
	if err != nil {
		return "", err
	}

	_, err = builder.WriteString(stats.String())
	if err != nil {
		return "", err
	}
	_, err = builder.WriteString(fmt.Sprintln("\nNo.,Name,Acc,Size"))
	if err != nil {
		return "", err
	}

	i := 0
	for _, b := range buckets {
		i++
		_, err = builder.WriteString(fmt.Sprintf("%15d,%s,%s\n", b.Stats.StorageBytes, b.Name, b.ProfileName))
		if err != nil {
			return "", err
		}
		if i == LIMIT {
			break
		}
	}
	return builder.String(), nil
}

// print details about top buckets
func ReportListLikeBucket(like []string, day string) (string, error) {
	buckets := []Bucket{}

	// aggregate profiles and collect buckets

	for _, p := range Profiles {
		for _, b := range p.Buckets {
			var cont bool
			for _, v := range like {
				if strings.Contains(b.Name, v) {
					cont = true
					break
				}
			}
			if cont {
				buckets = append(buckets, *b)
			}
		}
	}

	// sort to tget the top-10
	sort.Slice(buckets, func(i, j int) bool {
		return buckets[i].NonCurrentVersionStorageBytes > buckets[j].NonCurrentVersionStorageBytes
	})

	builder := strings.Builder{}
	_, err := builder.WriteString(fmt.Sprintf("S3 %s\n", day))
	if err != nil {
		return "", err
	}

	i := 0
	for _, b := range buckets {
		i++
		_, err = builder.WriteString(fmt.Sprintf("%02d. %s\n%s\n", i, b.Name, b.Stats))
		if err != nil {
			return "", err
		}
		if i == LIMIT {
			break
		}
	}
	return builder.String(), nil
}

// print stats of buckets like-string
func ReportLikeBucket(like []string, day string) (string, error) {
	buckets := []Bucket{}
	stats := Stats{}

	// aggregate profiles and collect buckets
	for _, p := range Profiles {
		for _, b := range p.Buckets {
			var cont bool
			for _, v := range like {
				if strings.Contains(b.Name, v) {
					cont = true
					break
				}
			}
			if cont {
				buckets = append(buckets, *b)
				stats.StorageBytes += b.StorageBytes
				stats.CurrentVersionStorageBytes += b.CurrentVersionStorageBytes
				stats.NonCurrentVersionStorageBytes += b.NonCurrentVersionStorageBytes
				stats.IncompleteMPUStorageBytesOlderThan7Days += b.IncompleteMPUStorageBytesOlderThan7Days
				stats.DeleteMarkerStorageBytes += b.DeleteMarkerStorageBytes
				stats.ObjectCount += b.ObjectCount
			}
		}
	}

	// sort to tget the top-10
	sort.Slice(buckets, func(i, j int) bool {
		return buckets[i].StorageBytes > buckets[j].StorageBytes
	})

	builder := strings.Builder{}
	_, err := builder.WriteString(fmt.Sprintf("S3 %s, LIKE: %s\n", day, like))
	if err != nil {
		return "", err
	}

	_, err = builder.WriteString(stats.String())
	if err != nil {
		return "", err
	}
	_, err = builder.WriteString(fmt.Sprintf("\n%s,%s,%s\n", "name", "env", "size"))
	if err != nil {
		return "", err
	}

	i := 1
	for _, b := range buckets {
		_, err = builder.WriteString(fmt.Sprintf("%s,%s,%s\n", b.Name, b.ProfileName, PrintBytes(b.Stats.StorageBytes)))
		if err != nil {
			return "", err
		}
		i++
	}
	return builder.String(), nil
}

``` 

make report-s3  
- S3 summary, including size and top 10 buckets
- query the S3-stg bucket data-devops-s3-reporting
- depends on AWS-OKTA  
s3-list.sh  
- list all s3 buckets  
- depends on AWS-OKTA
