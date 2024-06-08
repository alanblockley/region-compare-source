# Author: Alan Blockley
# Date: 2024-05-26
# ---

import os
import json
import boto3
import requests

URL = os.environ['JSON_URL']

if os.environ.get('AWS_SAM_LOCAL'):
    print("running in local")
    CURRENT_VERSION_PARAMETER = "/regional-services/current_version"
    CURRENT_SERVICES_BUCKET = "dbla-prod-region-compare-bucket-4b3jodtvv3ce"
else:
    CURRENT_VERSION_PARAMETER = os.environ['CURRENT_VERSION_PARAMETER']
    CURRENT_SERVICES_BUCKET = os.environ['CURRENT_SERVICES_BUCKET']

ssm = boto3.client('ssm')
s3 = boto3.client('s3')

def get_services(region):

    try:
        response = requests.get(URL)

    except requests.exceptions.RequestException as e:
        print(e)

    else:
        data = response.json()
        json_data = json.dumps(data['prices'], indent=4)
        json_dict = json.loads(json_data)

        print("Using version: ", data['metadata']['source:version'])
        services = [ entry for entry in json_dict if entry['attributes']['aws:region'] == region ]
        return services

def get_version():
    try:
        version = ssm.get_parameter(Name=CURRENT_VERSION_PARAMETER)
    except Exception as e:
        print(e)
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
        return version['Parameter']['Value']

def lambda_handler(event, context):

    print(event)
    region = event['pathParameters']['region']

    version = get_version()
    services = get_services(region)

    return {
        "statusCode": 200,
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },        
        "body": json.dumps({
            "version": version,
            "services": services,
        }),
    }    



