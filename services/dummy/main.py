

import json

import requests

from common import config

config.setup(__file__)

host = config.ServiceRegistry.get_service_hostname('tgbot')
port = config.ServiceRegistry.SERVICE_TGBOT_PORT

url = f'http://{host}:{port}/send_message'
data = {'target': '2186', 'message': 'hello from dummy service!'}
headers = {"Content-Type": "application/json"}


response = requests.post(url, data=json.dumps(data), headers=headers)
print(response.text)

