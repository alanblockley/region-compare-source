# backend resources for region compare.

Has code for following resources. 

--
  GetLLMListFunction:
    Type: AWS::Serverless::Function
--
  GetVersionFunction:
    Type: AWS::Serverless::Function
--
  GetRegionsFunction:
    Type: AWS::Serverless::Function
--
  GetNewsFunction:
    Type: AWS::Serverless::Function
--
  GetServicesByRegionFunction:
    Type: AWS::Serverless::Function
--
  IngestServicesDataFunction:
    Type: AWS::Serverless::Function
--
  GenerateServiceNewsFunction:
    Type: AWS::Serverless::Function
--
  GenerateServiceNewsQueue:
    Type: AWS::SQS::Queue
--
  ServiceNewsTable:
    Type: AWS::Serverless::SimpleTable
--
  RegionDataTable:
    Type: AWS::Serverless::SimpleTable
--
  Bucket:
    Type: AWS::S3::Bucket
--
  BucketPolicy:
    Type: AWS::S3::BucketPolicy
--
  DataBucket:
    Type: AWS::S3::Bucket
--
  DataBucketPolicy:
    Type: AWS::S3::BucketPolicy
--
  Originaccessidentity:
    Type: AWS::CloudFront::CloudFrontOriginAccessIdentity
--
  DataBucketOriginaccessidentity:
    Type: AWS::CloudFront::CloudFrontOriginAccessIdentity
--
  Distribution:
    Type: AWS::CloudFront::Distribution
--
  CurrentVersionParameter:
    Type: AWS::SSM::Parameter
--
  PreviousVersionParameter:
    Type: AWS::SSM::Parameter
--
  DNSEntry:
    Type: AWS::Route53::RecordSetGroup