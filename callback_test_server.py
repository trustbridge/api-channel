from flask import Flask, request, Response

app = Flask(__name__)


@app.route('/callback', methods=('GET',))
def callback_get():
    return Response(request.args['hub.challenge'])


@app.route('/callback', methods=('POST',))
def callback_post():
    app.logger.info("Received POST request, json:%s", request.json)
    return Response(status=200)
