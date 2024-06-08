# Author: Alan Blockley
# 
# ---

import os
import json
import boto3
import logging
import botocore
from decimal import Decimal

logger = logging.getLogger()
logger.setLevel(logging.INFO)

SERVICE_NEWS_TABLE = os.environ['SERVICE_NEWS_TABLE']
dynamodb = boto3.resource('dynamodb')

def lambda_handler(event, context):
    # Get all items from DDB table and paginate if needed
    table = dynamodb.Table(SERVICE_NEWS_TABLE)
    try:
        response = table.scan()
    except botocore.exceptions.ClientError as e:
        
        logger.info(e.response['Error']['Message'])

        error_code = e.response['Error']['Code']
        if error_code == 'AccessDeniedException':
            # Handle access denied error
            return {
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'statusCode': 403,
                'body': json.dumps({'error': 'Access denied to DynamoDB table'})
            }
        else:
            # Handle other DynamoDB errors
            return {
                'headers': {
                    'Access-Control-Allow-Origin': '*',
                    'Access-Control-Allow-Headers': 'Content-Type',
                    'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
                },
                'statusCode': 500,
                'body': json.dumps({'error': 'Error retrieving data from DynamoDB'})
            }        
    else:
        items = response['Items']

        # Paginate through all items if needed
        while 'LastEvaluatedKey' in response:
            response = table.scan(ExclusiveStartKey=response['LastEvaluatedKey'])
            items.extend(response['Items'])

        sorted_items = sorted(items, key=lambda x: x['created'], reverse=True)
    
        for item in sorted_items:
            for key, value in item.items():
                if isinstance(value, Decimal):
                    item[key] = float(value)

        return {
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "statusCode": 200,
            "body": json.dumps({
                "items": sorted_items
            })
        }
