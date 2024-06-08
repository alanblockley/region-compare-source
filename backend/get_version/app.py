# Author: Alan Blockley
# Date: 2024-05-26
# ---

import os
import json
import boto3

if os.environ.get('AWS_SAM_LOCAL'):
    print("running in local")
    CURRENT_VERSION_PARAMETER = "/regional-services/current_version"
    CURRENT_SERVICES_BUCKET = "dbla-prod-region-compare-bucket-4b3jodtvv3ce"
else:
    CURRENT_VERSION_PARAMETER = os.environ['CURRENT_VERSION_PARAMETER']
    CURRENT_SERVICES_BUCKET = os.environ['CURRENT_SERVICES_BUCKET']

ssm = boto3.client('ssm')

def lambda_handler(event, context):

    try:
        resource = ssm.get_parameter(Name=CURRENT_VERSION_PARAMETER)
    except Exception as e:
        return {
            "statusCode": 500,
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },        
            "body": json.dumps({
                "error": e
            }),
        }
    else:
        version = resource['Parameter']['Value']
    
        return {
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "statusCode": 200,
            "body": json.dumps({
                "version": version
            }),
        }            
    



