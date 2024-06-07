import json

regions = {}

with open('index-20230328172700.json') as f:
  data = json.load(f)

  for item in data['prices']:
    region = item["attributes"]["aws:region"] 
    service = item["attributes"]["aws:serviceName"]

    if region not in regions:
      regions[region] = []
      
    regions[region].append(service)

print('<table>')
print('<tr><th>Region</th><th>Services</th></tr>')

for region, services in regions.items():
  print(f'<tr><td>{region}</td><td>{", ".join(services)}</td></tr>')

print('</table>')
