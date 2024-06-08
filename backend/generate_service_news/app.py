# Author: Alan Blockley
# Date: 2024-05-26
# ---
# 
import os
import json
import boto3
import uuid
import time
import logging
import datetime

logger = logging.getLogger()
logger.setLevel("INFO")

if os.environ.get('AWS_SAM_LOCAL'):
    print("running in local")
    CURRENT_VERSION_PARAMETER = "/regional-services/current_version"
    PREVIOUS_VERSION_PARAMETER = "/regional-services/previous_version"
    CURRENT_SERVICES_BUCKET = "dbla-prod-region-compare-bucket-xfvwywzpckno"
    SNS_TOPIC = os.environ['SNS_TOPIC']
    SERVICE_NEWS_TABLE = "dbla-prod-region-compare-ServiceNewsTable-Y0OMMP7XZTDN"
else:
    CURRENT_VERSION_PARAMETER = os.environ['CURRENT_VERSION_PARAMETER']
    PREVIOUS_VERSION_PARAMETER = os.environ['PREVIOUS_VERSION_PARAMETER']
    CURRENT_SERVICES_BUCKET = os.environ['CURRENT_SERVICES_BUCKET']
    SNS_TOPIC = os.environ['SNS_TOPIC']
    SERVICE_NEWS_TABLE = os.environ['SERVICE_NEWS_TABLE']

ddb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime')

def generate_news_story(payload):
    # Using bedrock-runtime generate a news story via the claud 3 haiku model
    prompt = """Your purpose is to create a social media style news story for the release of new AWS services in regions.
The content of the post should reference the service being newly released into the region(s) mentioned and if possible the specific region including any user friendly information about that region.
An example input looks like this `AWS Elemental MediaLive has been added to region(s) me-central-1, us-east-1, ap-southeast-2, `.
Ensure the post is understanable by a range of audiences, including non-technial personas AND devleopers. 
The output should be a json structure with the following fields:
service: The name of the service that has been added to the region
announcement: A social media style news story about the new service
Create a structured set of data in json providing a summary of the the service and the benefits to the customers within the region.  Ensure that you target the personas of both developers and business executives.  Do not return any narrative language.
Before you provide any output, show your working in <scratchpad> XML tags.
JSON fields must be labelled service and announcement.

Attempt to identify any further reading resources and return these as resources

Example json structure is:

<json>
{
    "service": Service Title
    "announcement": Social media announcement of this service,
    "headline": Headline of this service announcement,
    "resources": [
        {
            "title": "Resource Title",
            "url": "https://example.com"
        }
    ]
}
</json>

Output the json structure as a string in <json> XML tags.  Do not return any narrative language.

"""

    response = bedrock_runtime.invoke_model(
        modelId='anthropic.claude-3-haiku-20240307-v1:0',
        contentType='application/json',
        accept='application/json',
        body=json.dumps({
            "anthropic_version": "bedrock-2023-05-31",
            "max_tokens": 1000,
            "system": prompt,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": payload['push_msg']
                        }
                    ]
                }
            ]
        })
    )

    print(response)
    return json.loads(response.get('body').read())

def extract_substring(text, trigger_str, end_str):
    # Find string between two values (Thanks for this Mike!)
    last_trigger_index = text.rfind(trigger_str)
    if last_trigger_index == -1:
        return ""
    next_end_index = text.find(end_str, last_trigger_index)
    if next_end_index == -1:
        return ""
    substring = text[last_trigger_index + len(trigger_str):next_end_index]
    return substring

def store_news(service, announcement, resources, headline):
    # Store the news story in DynamoDB
    
    key = str(uuid.uuid4())

    table = ddb.Table(SERVICE_NEWS_TABLE)
    table.put_item(
        Item={
            'id': key,
            'service': service,
            'announcement': announcement,
            'resources': resources,
            'headline': headline, 
            'date_announced': datetime.datetime.now().strftime("%Y-%m-%d"),
            'created': int(time.time())
        }
    )

def lambda_handler(event, context):

    # Lambda function is triggered via SQS

    logger.info("Event: " + str(event))
    body = json.loads(event['Records'][0]['body'])

    response_body = generate_news_story(body)
    summary = response_body['content'][0]['text']
    json_summary = json.loads(extract_substring(summary, "<json>", "</json>"))    
    print(json_summary)

    news_service = json_summary['service']
    news_announcement = json_summary['announcement']
    news_resources = json_summary['resources']
    news_headline = json_summary['headline']

    store_news(news_service, news_announcement, news_resources, news_headline)

    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "VERSION CURRENT: "
        }),
    }            
            



