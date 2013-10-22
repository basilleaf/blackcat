import os
from flask import Flask, request, redirect
import twilio.twiml

app = Flask(__name__)

@app.route("/", methods=['GET', 'POST'])
def hello():
    """Respond to incoming calls with a simple text message."""

    text_command = request.values.get('Body', None)

    resp = twilio.twiml.Response()
    resp.message("Hello, Mobile Monkey " + str(text_command))
    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)