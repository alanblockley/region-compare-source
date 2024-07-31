import os
import json
import boto3
import logging
import hashlib
import requests
import datetime
from botocore.config import Config
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')
ssm = boto3.client('ssm')

if os.environ.get('AWS_SAM_LOCAL'):
    print("running in local")
    URL = "https://api.regional-table.region-services.aws.a2z.com/index.json"
    CURRENT_VERSION_PARAMETER = "/regional-services/current_models_version"
    PREVIOUS_VERSION_PARAMETER = "/regional-services/previous_models_version"
    CURRENT_SERVICES_BUCKET = "dbla-prod-region-compare-databucket-xfvwywzpckno"
    CURRENT_MD5_PARAMETER = ""
    PUSHED_APP_SECRET = "PushedAppSecret-pTk6IrVM4bxO"
else:
    URL = os.environ['JSON_URL']
    CURRENT_VERSION_PARAMETER = os.environ['CURRENT_VERSION_PARAMETER']
    PREVIOUS_VERSION_PARAMETER = os.environ['PREVIOUS_VERSION_PARAMETER']
    CURRENT_SERVICES_BUCKET = os.environ['CURRENT_SERVICES_BUCKET']
    CURRENT_MD5_PARAMETER = os.environ.get('CURRENT_MD5_PARAMETER')
    PUSHED_APP_SECRET = os.environ.get('PUSHED_APP_SECRET')
    REGION_DATA_TABLE = os.environ['REGION_DATA_TABLE']

SNS_TOPIC = os.environ['SNS_TOPIC']

def get_bedrock_regions():
    # Get a list of regions that currently support bedrock from the source file
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
        logger.info(f"[{region}] {e.response['Error']['Code']} - {e.response['Error']['Message']}")
        return "NOT_FOUND"
    else:
        for model in res['modelSummaries']:
            # Only tracking ON_DEMAND models at the moment
            if "ON_DEMAND" in model['inferenceTypesSupported']:
                # This is here because Amazon had an ambigious name for this model.  
                # If this becomes more than a one off I'll have to do something else
                # - AB 13/Jul/2024
                if model['modelId'] == "amazon.titan-embed-text-v2:0":
                    model['modelName'] = "Titan Text Embeddings V2"

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
        return None
    else:
        return response['Item']

def index_llms():

    model_by_region = []
    regions_data = []
    unique_models = []

    # Get a list of regions that currently support bedrock
    regions = get_bedrock_regions()

    # For each region we're going to get the list of Foundational Models
    for region in regions:
        
        llms = get_llms(region['attributes']['aws:region'])

        if llms != "NOT_FOUND":
            print("Found llms in ", region['attributes']['aws:region'])
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
        print("Region: ", region['region'])
        for llm in region['llms']:
            model_info = (llm['modelName'], llm['modelId'])
            # model_info = (llm['modelId'])
            unique_models.add(model_info)

    unique_model_list = sorted(unique_models, key=lambda x: x[0])

    data = {
        "unique_model_list": unique_model_list, 
        "model_by_region": model_by_region,
        "regions_data": regions_data
    }

    return data

def get_current_version_parameter():

    logger.info("get_previous_version")

    try:
        response = ssm.get_parameter(
            Name=CURRENT_VERSION_PARAMETER,
        )
    except Exception as e:
        logger.error(e)
        raise e

    previous_version = response['Parameter']['Value']

    return previous_version

def update_version(current_version):

    logger.info("update_version")
    logger.info("Setting version " + current_version + " on " + CURRENT_VERSION_PARAMETER)

    previous_version = get_current_version_parameter()

    # Set previous version
    try:
        ssm.put_parameter(
            Name=PREVIOUS_VERSION_PARAMETER,
            Value=previous_version,
            Overwrite=True,
        )
    except Exception as e:
        logger.error(e)
        raise e

    # Set current version
    try:
        ssm.put_parameter(
            Name=CURRENT_VERSION_PARAMETER,
            Value=current_version,
            Overwrite=True,
        )
    except Exception as e:
        logger.error(e)
        raise e

    return current_version    

    
def store_data(data, version):

    logger.info("store_data")

    try:
        s3.put_object(
            Body=json.dumps(data, indent=4),
            Bucket=CURRENT_SERVICES_BUCKET,
            Key="data/models/" + version + ".json"
        )
    except ClientError as e:
        print("error storing version data")
        raise e
    else:
        print("Stored: " + version + ".json")

    try:
        s3.put_object(
            Body=json.dumps(data, indent=4),
            Bucket=CURRENT_SERVICES_BUCKET,
            Key="data/models/latest.json"
        )
    except ClientError as e:
        print("error storing latest data")
        raise e
    else:
        print("Stored: latest.json")
    
    md5 = hashlib.md5(json.dumps(data, indent=4).encode("utf-8")).hexdigest()

    try:
        ssm.put_parameter(
            Name=CURRENT_MD5_PARAMETER,
            Value=md5,
            Overwrite=True,
        )
    except ClientError as e:
        print("error storing version")
        raise e
    else:
        print("Stored: " + md5)

def check_version(data):

    try:
        stored_md5 =  ssm.get_parameter(
            Name=CURRENT_MD5_PARAMETER,
        )

    except ClientError as e:
        print(e)
        return False
    
    else:
        print(stored_md5['Parameter']['Value'])

        md5 = hashlib.md5(json.dumps(data, indent=4).encode("utf-8")).hexdigest()
        print(md5)

        if (md5 != stored_md5['Parameter']['Value']):
            print("New version available")
            return True
        else:
            return False

def send_sns(subject, msg):
    
    print("send_sns: " + subject + " | " + msg)
    sns = boto3.client('sns')
    
    try:
        response = sns.publish(
            TopicArn=SNS_TOPIC,
            Message='\n\n' + subject + '\n\n --- \n\n' + msg,
            Subject=subject
        )
    except Exception as e:
        print(e)
        raise e
    else:
        print(response)
        return True

def compare_data(current_data, previous_version):

    try:
        res = s3.get_object(
            Bucket=CURRENT_SERVICES_BUCKET,
            Key="data/models/" + previous_version + ".json"
        )
    except ClientError as e:
        print(e)
        raise e
    else:
        previous_data = json.loads(res['Body'].read().decode('utf-8'))    

    new_models = []
    removed_models = []
    email_msg = ""
    gossip_msg = []

    for current_region in current_data['model_by_region']:
        print(f"Region: {current_region['region']}")
        for previous_region in previous_data['model_by_region']:
            if current_region['region'] == previous_region['region']:
                c = len(current_region['llms'])
                p = len(previous_region['llms'])

                if c > p:
                    for model in current_region['llms']:
                        if model not in previous_region['llms']:
                            new_models.append({
                                current_region['region'] : [f"{model['modelName']} ({model['modelId']})"]
                            })
                            email_msg = email_msg + f"{model['modelName']} ({model['modelId']}) has been added to region {current_region['region']}\n"
                            gossip_msg.append(f"{model['modelName']} ({model['modelId']}) has been added to region {current_region['region']})")
                if c < p:
                    for model in previous_region['llms']:
                        if model not in current_region['llms']:
                            removed_models.append({
                                current_region['region'] : [f"{model['modelName']} ({model['modelId']})"]
                            })
                            print(f"Removed model: {model}")
                if c == p:
                    print("No change")


def lambda_handler(event, context):

    # Create a version number based on YYYYMMDDHHMMSS
    version = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    previous_version = get_current_version_parameter()

    try:
        data = index_llms()
    except Exception as e:
        print(e)
        raise e

    if check_version(data):

        try:
            update_version(version)
        except Exception as e:
            print(e)
            raise e
                
        try:
            store_data(data, version)
        except Exception as e:
            print(e)
            raise e

        try:
            compare_data(data, previous_version)
        except Exception as e:
            print(e)
            raise e
        
    else:
        return "OK"