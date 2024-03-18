# main.py
from flask import Flask, request

app = Flask(__name__)


@app.route("/")
def hello_world():
    headers = dict(request.headers)
    cookies = request.cookies
    print("Headers:", headers)
    print("Cookies:", cookies)
    return {"headers": headers, "cookies": dict(cookies)}
