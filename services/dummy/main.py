import json

import requests

from common import config

config.setup(__file__)

host = config.ServiceRegistry.get_service_hostname("tgbot")
port = config.ServiceRegistry.SERVICE_TGBOT_PORT

url = f"https://{host}:{port}/enqueue_command"
data = {"task": "send_message_admin", "data": {"text": "test message"}}
headers = {"Content-Type": "application/json"}


response = requests.post(url, data=json.dumps(data), headers=headers, verify=False)
print(response.text)
