

from flask import Flask, request, jsonify


app = Flask(__name__)


def run_flask_app():
    app.run(host='0.0.0.0', debug=False, ssl_context='adhoc')


@app.route('/send_message', methods=['POST'])
def send_message():
    data = request.json
    print(f'received cmd to send message to {data["target"]}: {data["message"]}')
    return jsonify({'status': 'success', 'message': 'command processed'})
