import os
import json
import boto3
import logging
import datetime
import requests

# Setup the environment
logger = logging.getLogger()
logger.setLevel("INFO")

URL = os.environ['JSON_URL']

if os.environ.get('AWS_SAM_LOCAL'):
    print("running in local")
    CURRENT_VERSION_PARAMETER = "/regional-services/current_version"
    PREVIOUS_VERSION_PARAMETER = "/regional-services/previous_version"
    CURRENT_SERVICES_BUCKET = "dbla-prod-region-compare-databucket-xfvwywzpckno"
    PUSHED_APP_SECRET = "PushedAppSecret-pTk6IrVM4bxO"
else:
    CURRENT_VERSION_PARAMETER = os.environ['CURRENT_VERSION_PARAMETER']
    PREVIOUS_VERSION_PARAMETER = os.environ['PREVIOUS_VERSION_PARAMETER']
    CURRENT_SERVICES_BUCKET = os.environ['CURRENT_SERVICES_BUCKET']
    PUSHED_APP_SECRET = os.environ.get('PUSHED_APP_SECRET')

SNS_TOPIC = os.environ['SNS_TOPIC']
SQS_QUEUE = os.environ['SQS_QUEUE']

# Create AWS connections to services
ssm = boto3.client('ssm')
s3 = boto3.client('s3')
sqs = boto3.client('sqs')
sm = boto3.client('secretsmanager')

# Start functions
def get_data():
    response = requests.get(URL)
    data = response.json()
    return data

def update_version(data, current_version, previous_version):

    logger.info("update_version")
    logger.info("Setting version " + current_version + " on " + CURRENT_VERSION_PARAMETER)

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

def update_services(data):

    logger.info("update_services")
    # services = []

    json_data = json.dumps(data['prices'], indent=4)
    json_dict = json.loads(json_data)    

    unique_service_names = {entry["id"].split(":")[0]: entry["attributes"]["aws:serviceName"] for entry in json_dict}
    unique_service_names = dict(sorted(unique_service_names.items()))
    # for service_name in unique_service_names:
        
    #     print(service_name)
    #     services.append(service_name)
        
    try:
        s3_res = s3.put_object(
            Body=json.dumps(unique_service_names),
            Bucket=CURRENT_SERVICES_BUCKET,
            Key='data/services.json'
        )
    except Exception as e:
        print(e)
        return False
    else:
        print(s3_res)
        return True

def store_data(data):

    logger.error("store_data", data)

    version = data['metadata']['source:version']

    print("storing version " + version + "of data in s3")

    try:
        s3.put_object(
            Body=json.dumps(data),
            Bucket=CURRENT_SERVICES_BUCKET,
            Key="data/" + version+'.json'
        )
    except Exception as e:
        print(e)
        raise e
    else:
        return True
    
def store_gossip(push_msg, version):

    logger.info("store_gossip")

    logger.info("### push_msg")
    logger.info(push_msg)

    try:
        res = s3.get_object(
            Bucket=CURRENT_SERVICES_BUCKET,
            Key='data/gossip.json'
        )
    except Exception as e:
        logger.exception(e)
        raise e
    else:        
        data = json.load(res['Body'])
        logger.info("### data")
        logger.info(data)

        for gossip in push_msg:
            logger.info("### gossip")
            logger.info(gossip)

            data.append({
                "push_msg": gossip,
                "timestamp": datetime.datetime.now().isoformat(),
                "version": version
            })

            logger.info("### data")
            logger.info(data)

        try:
            s3.put_object(
                Body=json.dumps(data),
                Bucket=CURRENT_SERVICES_BUCKET,
                Key='data/gossip.json'
            )
        except Exception as e:
            print(e)
            raise e
        else:
            return True

def find_service_regions(service_name, payload):
    for entry in payload:
        if entry['service'] == service_name:
            return entry['regions']
    return None

def append_region_to_service(service_name, new_region, payload):
    for entry in payload:
        if entry['service'] == service_name:
            if new_region not in entry['regions']:
                entry['regions'].append(new_region)
            return entry
    return None

def get_push_secret():

    try:
        res = sm.get_secret_value(
            SecretId=PUSHED_APP_SECRET        
        )
    except Exception as e:
        logger.exception(e)
        return False
    else:
        return res['SecretString']
    
def send_push(msg):

    try:
        app_config = get_push_secret()
    except Exception as e:
        print("Unable to send push notification - Issue retrieving secrets")
        logger.exception(e)
        return False
    else:
        app_config = json.loads(app_config)

        print("send_push: " + msg)
        payload = {
            "app_key": app_config["PUSHED_APP_KEY"],
            "app_secret": app_config["PUSHED_APP_SECRET"],
            "target_type": "app",
            "content": msg
        }

        r = requests.post("https://api.pushed.co/1/push", data=payload)
        print(r.text)

        return True

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

    logger.info("compare_data")

    res = s3.get_object(
        Bucket=CURRENT_SERVICES_BUCKET,
        Key="data/" + previous_version+'.json'
    )
    previous_data = json.load(res['Body'])
    
    current = current_data['prices']
    previous = previous_data['prices']    

    current_service_ids = []
    for service in current:
        current_service_ids.append(service['id'])

    previous_service_ids = []
    for service in previous:
        previous_service_ids.append(service['id'])

    print("Previous Services:", len(previous_service_ids))
    print("Current Services:", len(current_service_ids))

    if len(current_service_ids) == len(previous_service_ids):
        logger.error("The number of services is the same - nothing to do")
        return False
    if len(current_service_ids) < len(previous_service_ids):
        logger.error("The number of services is less - nothing to do")
        return False
    
    i = 0
    affected_regions = []
    email_msg = ""
    gossip_msg = []
    news_payload = []

    for service in current_service_ids:
        if service not in previous_service_ids:
            
            for current_service_data in current:
                if current_service_data['id'] == service:
                    service_name = current_service_data['attributes']['aws:serviceName']
                    region_name = current_service_data['attributes']['aws:region']
                    affected_regions = affected_regions + [region_name]
                    break
            
            email_msg = email_msg + "%s has been added to region %s\n" % (service_name, region_name)
            gossip_msg.append("%s has been added to region %s" % (service_name, region_name))

            regions = find_service_regions(service_name, news_payload)

            if regions:
                if region_name in regions:
                    print(f"The service is already available in the region {region_name}")
                else:
                    append_region_to_service(service_name, region_name, news_payload)

                print(f"The regions for the service '{service_name}' are: {regions}")
            else:
                news_payload.append({'service': service_name, 'regions' : [ region_name ]})

    print(news_payload)

    for news in news_payload:
        i = i + 1
        news_msg = news['service'] + " has been added to region(s) "
        for region in news['regions']:
            news_msg += region + ", "

        now = datetime.datetime.strptime(current_data['metadata']['source:version'], "%Y%m%d%H%M%S")
        news_date_string = now.strftime('%Y-%m-%dT%H:%M:%S')
        print(news_date_string)

        news_sqs_payload = {
            "push_msg": news['service'],
            "timestamp": news_date_string,
            "version": current_data['metadata']['source:version']
        }

        print("Sending payload to SQS Queue")
        
        sqs.send_message(
            QueueUrl=SQS_QUEUE,
            MessageBody=json.dumps(news_sqs_payload)
        )
            
    print("---\n\n" + email_msg + "\n---")
    push_msg = f"{str(i)} AWS Service(s) were added across {str(len(set(affected_regions)))} regions"
    store_gossip(gossip_msg, current_data['metadata']['source:version'])
    
    print(push_msg)

    send_push(str(push_msg))
    send_sns(push_msg, email_msg)

    return True
    
def lambda_handler(event, context):
    
    try:
        data = get_data()
    except Exception as e:
        print(e)
        raise e
    else:
        # Get the current version from SSM Parameter store
        version = ssm.get_parameter(
            Name=CURRENT_VERSION_PARAMETER,
        )
        version = version['Parameter']['Value']

        if version != data['metadata']['source:version']:

            current_version = data['metadata']['source:version']
            previous_version = version
            
            print("Current Version: " + current_version)
            print("Previous Version: " + previous_version)

            try:
                update_version(data, current_version, previous_version)
            except Exception as e:
                print(e)
                raise e
            
            try:
                store_data(data)
            except Exception as e:
                print(e)
                raise e

            try:
                compare_data(data, previous_version)
            except Exception as e:
                print(e)
                raise e

            try:
                update_services(data)
            except Exception as e:
                print(e)
                raise e
    
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "VERSION UPDATED: " + version
                }),
            }
        else:
            return {
                "statusCode": 200,
                "body": json.dumps({
                    "message": "VERSION CURRENT: " + version
                }),
            }            
            



