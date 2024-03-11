

import json

import requests

from common import config

config.setup(__file__)

host = config.ServiceRegistry.get_service_hostname('tgbot')
port = config.ServiceRegistry.SERVICE_TGBOT_PORT

url = f'http://{host}:{port}/enqueue_command'
data = {
    'command': 'send_message',
    'data': {
        'chat_id': 1234,
        'text': 'test message'
    }
}
headers = {"Content-Type": "application/json"}


response = requests.post(url, data=json.dumps(data), headers=headers, verify=False)
print(response.text)

