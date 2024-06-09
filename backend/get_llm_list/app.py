# Author: Alan Blockley
# Date:
# ---

import os
import json
import boto3
import logging
import requests
from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

URL = os.environ['JSON_URL']
dynamodb = boto3.resource('dynamodb')

REGION_DATA_TABLE = os.environ['REGION_DATA_TABLE']

def get_bedrock_regions():
    
    regions = []

    response = requests.get(URL)
    data = response.json()

    json_data = json.dumps(data['prices'], indent=4)
    json_dict = json.loads(json_data)    

    regions = [ entry for entry in json_dict if entry['attributes']['aws:serviceName'] == 'Amazon Bedrock']

    return regions

def get_llms(region):

    llms = []

    bedrock_config = Config(
        region_name=region,
    )
    
    bedrock = boto3.client('bedrock', config=bedrock_config)

    try:
        res = bedrock.list_foundation_models()
    except ClientError as e:
        print("Bedrock not found in", region)
        return "NOT_FOUND"
    else:
        for model in res['modelSummaries']:
            if "ON_DEMAND" in model['inferenceTypesSupported']:
                llms.append({
                    "modelName" : model['modelName'],
                    "modelArn" : model['modelArn'],
                    "modelId" : model['modelId']
                })
    return llms

def get_region_data(region):
    # Get Region data from DDB table using region as id
    table = dynamodb.Table(REGION_DATA_TABLE)
    try:
        response = table.get_item(Key={'id': region})
    except ClientError as e:
        logger.info("No access to Bedrock in " + region)
        print(e.response['Error']['Message'])
        return None
    else:
        print(response)
        return response['Item']

    

def lambda_handler(event, context):
    # Get all items from DDB table and paginate if needed

    model_by_region = []
    regions_data = []

    regions = get_bedrock_regions()

    for region in regions:
        print("Region", region['attributes']['aws:region'])
        
        llms = get_llms(region['attributes']['aws:region'])
        print("LLM:", llms)

        if llms == "NOT_FOUND":
            logger.info("No access to Bedrock in " + region['attributes']['aws:region'])
        else:
            model_by_region.append({
                'region' : region['attributes']['aws:region'],
                'llms': llms
             })

            region_data = get_region_data(region['attributes']['aws:region'])
            if region_data:
                regions_data.append({
                    'id' : region_data['id'],
                    'name' : region_data['name'],
                    'continent' : region_data['continent']
                })
    
    # Create a set to store unique model names and IDs
    unique_models = set()

    # Iterate through the regions and LLMs
    for region in model_by_region:
        for llm in region['llms']:
            model_info = (llm['modelName'], llm['modelId'])
            unique_models.add(model_info)

    # Convert the set to a list and print the results
    unique_model_list = list(unique_models)
    for model_name, model_id in unique_model_list:
        print(f"Model Name: {model_name}, Model ID: {model_id}")

    unique_model_list = sorted(unique_model_list, key=lambda x: x[0])

    return {
            'headers': {
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type',
                'Access-Control-Allow-Methods': 'OPTIONS,POST,GET'
            },
            "statusCode": 200,
            "body": json.dumps({
                "unique_model_list": unique_model_list,
                "regions": model_by_region, 
                "region_data" : regions_data
            })
        }
