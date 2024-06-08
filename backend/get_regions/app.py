# Author: Alan Blockley
# Date: 2024-05-26
# ---

import os
import json
import boto3

REGION_DATA_TABLE = os.environ['REGION_DATA_TABLE']

account = boto3.client('account')
dynamodb = boto3.client('dynamodb')

def lambda_handler(event, context):

    account_resource = account.list_regions(MaxResults=50)

    regions = []

    count = 0
    for region in account_resource['Regions']:
        regions.append(region['RegionName'])
        count += 1

    print("{} regions returned".format(count))

    region_data = []
    
    ddb_response = dynamodb.scan(TableName=REGION_DATA_TABLE)
    for item in ddb_response['Items']:
        region_data.append({
            'id' : item['id']['S'],
            'name' : item['name']['S'],
            'continent' : item['continent']['S']
        })
        print(item)
    
    return {
        'headers': {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type',
            'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
        },
        "statusCode": 200,
        "body": json.dumps({
            "regions": regions, 
            "region_data": region_data
        }),
    }            
    



