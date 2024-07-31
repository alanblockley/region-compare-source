import os
import json
import boto3
import uuid
import time
import logging
import datetime
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel("INFO")

if os.environ.get('AWS_SAM_LOCAL'):
    print("running in local")
    CURRENT_VERSION_PARAMETER = "/regional-services/current_version"
    PREVIOUS_VERSION_PARAMETER = "/regional-services/previous_version"
    CURRENT_SERVICES_BUCKET = "dbla-prod-region-compare-bucket-xfvwywzpckno"
    SNS_TOPIC = os.environ['SNS_TOPIC']
    SERVICE_NEWS_TABLE = "dbla-prod-region-compare-ServiceNewsTable-Y0OMMP7XZTDN"
    MODEL='anthropic.claude-3-haiku-20240307-v1:0'
    GENERATE_RSS_FEED_FUNCTION=""
    
else:
    CURRENT_VERSION_PARAMETER = os.environ['CURRENT_VERSION_PARAMETER']
    PREVIOUS_VERSION_PARAMETER = os.environ['PREVIOUS_VERSION_PARAMETER']
    CURRENT_SERVICES_BUCKET = os.environ['CURRENT_SERVICES_BUCKET']
    SNS_TOPIC = os.environ['SNS_TOPIC']
    SERVICE_NEWS_TABLE = os.environ['SERVICE_NEWS_TABLE']
    MODEL='anthropic.claude-3-haiku-20240307-v1:0'
    GENERATE_RSS_FEED_FUNCTION=os.environ['GENERATE_RSS_FEED_FUNCTION']


ddb = boto3.resource('dynamodb')
bedrock_runtime = boto3.client('bedrock-runtime')
lambda_client = boto3.client('lambda')

def check_json(json_string):

    prompt = """
Your task is to validate the provided JSON input and ensure it conforms to the expected structure and format. The JSON input will be enclosed within <json> ... </json> tags, and you should assume that only the content within these tags will be provided as input.

The expected JSON structure is as follows:

{
  "service": string, // The name of the AWS service released in the new region(s)
  "announcement": string, // A social media-style announcement about the service release
  "headline": string, // A concise headline for the announcement
  "summary": string, // A brief summary of the service's key features and benefits, targeted at developers and technical users
  "businessBenefits": array of strings, // A list of key benefits for business executives and non-technical stakeholders
  "resources": array of objects, // An array of relevant resources with titles and URLs
  "resources[].title": string, // The title of the resource
  "resources[].url": string // The URL of the resource
}

Your output should be a single string:

- If the provided JSON is valid and conforms to the expected structure, return the string "Valid JSON".
- If the provided JSON is invalid or does not conform to the expected structure, return the string "Invalid JSON".

You do not need to provide any additional information or explanation in your output. Simply return "Valid JSON" or "Invalid JSON" based on the validity and structure of the input JSON.

Example valid input:
<json>
{
  "service": "AWS Elemental MediaLive",
  "announcement": "AWS Elemental MediaLive, a highly reliable live video processing service, is now available in the Middle East, Northern Virginia, and Sydney regions...",
  "headline": "AWS Elemental MediaLive Launches in New Regions",
  "summary": "AWS Elemental MediaLive is a cloud service that lets you create live outputs for broadcast and streaming delivery...",
  "businessBenefits": [
    "Cost-effective live video processing",
    "Reliable and scalable live video infrastructure",
    "Global availability for broad reach"
  ],
  "resources": [
    {
      "title": "AWS Elemental MediaLive Documentation",
      "url": "https://docs.aws.amazon.com/medialive/latest/ug/what-is.html"
    },
    {
      "title": "AWS Elemental MediaLive Pricing",
      "url": "https://aws.amazon.com/medialive/pricing/"
    }
  ]
}
</json>

"""
    try:
        response = bedrock_runtime.converse(
            modelId=MODEL,
            system=[
                {
                    "text": prompt
                }
            ],
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"text": json_string}
                    ]
                }
            ]
        )
    except ClientError as e:
        logger.error(f"[check_json] Error calling Bedrock Runtime: {e.response['Error']['Message']}")
        return 'Invalid JSON'
    except Exception as e:
        logger.error(f"[check_json] Error calling Bedrock Runtime: {e}")
        return 'Invalid JSON'
    else:
        logger.info(f"Bedrock Runtime response: {response}")

        print(response['output']['message']['content'][0]['text'])
        if response['output']['message']['content'][0]['text'] == 'Valid JSON':
            logger.info("Returning Valid JSON")
            return 'Valid JSON'
        else:
            logger.info("Returning Invalid JSON")
            return 'Invalid JSON'

def generate_news_story(payload):
    # Using bedrock-runtime generate a news story via the claud 3 haiku model

    prompt = """
Your task is to generate a social media announcement for the release of new AWS services in specific regions. Follow these guidelines:

1. The announcement should reference the service being newly released and the specific region(s) it's available in. Include user-friendly information about the region(s), such as its geographical location or notable characteristics.

2. Ensure the announcement is understandable to both non-technical audiences and developers.

3. Avoid using double quotes ("), single quotes ('), emojis, or HTML tags in the announcement.

4. Structure the output as a JSON object with the following fields:
   - service: The name of the service released in the new region(s).
   - announcement: A social media-style announcement about the service release, written for a general audience.
   - headline: A concise headline for the announcement.
   - summary: A brief summary of the service's key features and benefits, targeted at developers and technical users.
   - businessBenefits: A list of key benefits for business executives and non-technical stakeholders.
   - resources: An array of relevant resources (documentation, pricing, etc.) with titles and URLs.

5. Focus the announcement primarily on the new region availability rather than the service itself.

6. Provide your JSON output enclosed within <json> ... </json> tags, with no additional narrative.

Example input:
AWS Elemental MediaLive has been added to region(s) me-central-1 (Middle East), us-east-1 (Northern Virginia), ap-southeast-2 (Sydney).

Example output (enclosed in <json> ... </json> tags):
<json>
{
  "service": "AWS Elemental MediaLive",
  "announcement": "AWS Elemental MediaLive, a highly reliable live video processing service, is now available in the Middle East, Northern Virginia, and Sydney regions. Creators and broadcasters in these areas can now easily create high-quality live video streams for various platforms and devices.",
  "headline": "AWS Elemental MediaLive Launches in New Regions",
  "summary": "AWS Elemental MediaLive is a cloud service that lets you create live outputs for broadcast and streaming delivery... [summary of key features]",
  "businessBenefits": [
    "Cost-effective live video processing",
    "Reliable and scalable live video infrastructure",
    "Global availability for broad reach"
  ],
  "resources": [
    {
      "title": "AWS Elemental MediaLive Documentation",
      "url": "https://docs.aws.amazon.com/medialive/latest/ug/what-is.html"
    },
    {
      "title": "AWS Elemental MediaLive Pricing",
      "url": "https://aws.amazon.com/medialive/pricing/"
    }
  ]
}
</json>
"""
    try:
        response = bedrock_runtime.invoke_model(
            modelId=MODEL,
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
    except ClientError as e:
        logger.error(f"[generate_news_story] Error calling Bedrock Runtime: {e.response['Error']['Message']}")
        raise e
    except Exception as e:
        logger.error(f"[generate_news_story] Error calling Bedrock Runtime: {e}")
        raise e
    else:
        logger.info(f"Bedrock Runtime response: {response}")
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

# Not in production yet (preview)
def generate_rss_feed():
    try:
        lambda_client.invoke(
            FunctionName=GENERATE_RSS_FEED_FUNCTION,
            InvocationType='Event',
        )
    except ClientError as e:
        logger.error(f"[generate_rss_feed] Error calling Lambda function: {e.response['Error']['Message']}")
        raise e
    else:
        logger.info("[generate_rss_feed] Successfully invoked Lambda function")
        return True
    
def lambda_handler(event, context):

    # Lambda function is triggered via SQS
    
    print(boto3.__version__)
    valid_json = False

    logger.info("Event: " + str(event))
    body = json.loads(event['Records'][0]['body'])

    while valid_json == False:
        # Generate news story
        response_body = generate_news_story(body)
        summary = response_body['content'][0]['text']
        json_summary = json.loads(extract_substring(summary, "<json>", "</json>"))    
        if check_json(json.dumps(json_summary)) == "Valid JSON":
            valid_json = True
            break

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
            



