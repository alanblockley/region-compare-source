import boto3

# CSV data embedded directly in the script
csv_data = """Region Code,Friendly Name,Continent
us-east-1,N. Virginia,North America
us-east-2,Ohio,North America
us-west-1,N. California,North America
us-west-2,Oregon,North America
ca-central-1,Canada Central,North America
eu-west-1,Ireland,Europe
eu-west-2,London,Europe
eu-west-3,Paris,Europe
eu-central-1,Frankfurt,Europe
eu-north-1,Stockholm,Europe
eu-south-1,Milan,Europe
eu-south-2,Spain,Europe
ap-northeast-1,Tokyo,Asia
ap-northeast-2,Seoul,Asia
ap-northeast-3,Osaka,Asia
ap-southeast-1,Singapore,Asia
ap-southeast-2,Sydney,Australia
ap-southeast-3,Jakarta,Asia
ap-southeast-4,Melbourne,Australia
ap-south-1,Mumbai,Asia
ap-south-2,Hyderabad,Asia
sa-east-1,São Paulo,South America
af-south-1,Cape Town,Africa
me-south-1,Bahrain,Middle East
me-central-1,UAE,Middle East"""

def update_data():
    # Split the CSV data into lines
    lines = csv_data.strip().split('\n')
    
    # Extract the header
    headers = lines[0].split(',')
    
    # Iterate over the remaining lines
    for line in lines[1:]:

        values = line.split(',')
        item = {headers[i]: values[i] for i in range(len(headers))}
        
        print("Updating ", item['Region Code'])

        # Update item in DynamoDB table
        table.update_item(
            Key={
                'id': item['Region Code']
            },
            UpdateExpression="SET #name = :friendlyName, continent = :continent",
            ExpressionAttributeValues={
                ':friendlyName': item['Friendly Name'],
                ':continent': item['Continent']
            },
            ExpressionAttributeNames={
                "#name": "name"
            }
        )
        
        print(f"Updated {item['Region Code']} - {item['Friendly Name']} - {item['Continent']}")

def check_table_exists():
    
    # Check if the table exists
    try:
        table.load()
        return True
    except:
        return False
    
if __name__ == "__main__":

    dynamodb = boto3.client('dynamodb')

    list_table_rest = dynamodb.list_tables()
    print(list_table_rest)

    if check_table_exists():
        print('Table exists.')
    else:
        print('Table does not exist.')
        exit()

    update_data()
    print('Data update complete.')
