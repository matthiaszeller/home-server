import asyncio
import logging

from quart import Quart, jsonify, request

# TODO: security of who can interact with bot

app = Quart(__name__)
message_queue: asyncio.Queue = None


async def run_flask_app(shared_queue: asyncio.Queue):
    global message_queue
    message_queue = shared_queue
    try:
        await app.run_task(host='0.0.0.0', debug=False)
    except asyncio.CancelledError:
        logging.info('api server shut down')


@app.route('/enqueue_command', methods=['POST'])
async def enqueue_command():
    command_message = await request.get_json()

    await message_queue.put(command_message)
    return jsonify({'status': 'success', 'message': 'Command enqueued'})
