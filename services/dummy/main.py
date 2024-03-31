from common import config

config.setup(__file__)

from common.api import TgbotAPI  # noqa E402

data = {"task": "send_message_admin", "data": {"text": "test message"}}

response = TgbotAPI.post("/enqueue_task", data, verify=False)
print(response.status_code, response.text)
