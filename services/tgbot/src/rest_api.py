import asyncio
import logging

from quart import Quart, jsonify, request

from common.config import PathRegistry as PR

app = Quart(__name__)
message_queue: asyncio.Queue = None


async def run_flask_app(shared_queue: asyncio.Queue):
    global message_queue
    message_queue = shared_queue
    try:
        path_cert = PR.get_config_file("secrets/certificate.pem")
        path_key = PR.get_config_file("secrets/key.pem")
        await app.run_task(
            host="0.0.0.0", debug=False, certfile=path_cert, keyfile=path_key
        )
    except asyncio.CancelledError:
        logging.info("api server shut down")


@app.route("/enqueue_command", methods=["POST"])
async def enqueue_command():
    command_message = await request.get_json()

    await message_queue.put(command_message)
    return jsonify({"status": "success", "message": "Command enqueued"})
