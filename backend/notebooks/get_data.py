# %%
import os
import json
import requests

# %%
URL = "https://api.regional-table.region-services.aws.a2z.com/index.json"

# %%
response = requests.get(URL)

# %%
data = response.json()

# %%
json_data = json.dumps(data['prices'], indent=4)
json_dict = json.loads(json_data)

# %%
print(json_data)

# %%
print(json_dict)

# %%
region_left = [ entry for entry in json_dict if entry['attributes']['aws:region'] == 'ap-southeast-2' ]
region_right = [ entry for entry in json_dict if entry['attributes']['aws:region'] == 'eu-west-1' ]

print(region_left)

# %%
unique_service_names = set(entry["attributes"]["aws:serviceName"] for entry in json_dict)

# %%
print(unique_service_names)

# %%
for unique_service in unique_service_names:
    for service in region_right:
        print(service)
        if service['attributes']['aws:serviceName'] == unique_service:
            print(service['name'], service['region'])
            break

# %%



