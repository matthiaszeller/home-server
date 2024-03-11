import asyncio
import logging
import queue

from flask import Flask, request, jsonify

# TODO: security of who can interact with bot

app = Flask(__name__)
message_queue: asyncio.Queue = None
event_loop: asyncio.BaseEventLoop = None


def run_flask_app(shared_queue: asyncio.Queue, _event_loop: asyncio.BaseEventLoop):
    global message_queue, event_loop
    message_queue = shared_queue

    app.run(host='0.0.0.0', debug=False, ssl_context='adhoc')


@app.route('/enqueue_command', methods=['POST'])
def enqueue_command():
    command_message = request.json

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    future = asyncio.run_coroutine_threadsafe(message_queue.put(command_message), loop)
    logging.debug('before result')
    future.result()  # Optional: Wait for the item to be enqueued
    logging.debug('after result')
    return jsonify({'status': 'success', 'message': 'Command enqueued'})

