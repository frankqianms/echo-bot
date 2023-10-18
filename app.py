# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.

import sys
import traceback
from datetime import datetime
import logging
# from http import HTTPStatus

# from aiohttp import web
# from aiohttp.web import Request, Response, json_response
from botbuilder.core import (
    BotFrameworkAdapterSettings,
    TurnContext,
    BotFrameworkAdapter,
)
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.schema import Activity, ActivityTypes
import jwt

from bots import EchoBot
from config import DefaultConfig
from test import decode_auth_header

CONFIG = DefaultConfig()

# Create adapter.
# See https://aka.ms/about-bot-adapter to learn more about how bots work.
SETTINGS = BotFrameworkAdapterSettings(CONFIG.APP_ID, CONFIG.APP_PASSWORD)
ADAPTER = BotFrameworkAdapter(SETTINGS)


# Catch-all for errors.
async def on_error(context: TurnContext, error: Exception):
    # This check writes out errors to console log .vs. app insights.
    # NOTE: In production environment, you should consider logging this to Azure
    #       application insights.
    print(f"\n [on_turn_error] unhandled error: {error}", file=sys.stderr)
    traceback.print_exc()

    # Send a message to the user
    await context.send_activity("The bot encountered an error or bug.")
    await context.send_activity(
        "To continue to run this bot, please fix the bot source code."
    )
    # Send a trace activity if we're talking to the Bot Framework Emulator
    if context.activity.channel_id == "emulator":
        # Create a trace activity that contains the error object
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.utcnow(),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
        )
        # Send a trace activity, which will be displayed in Bot Framework Emulator
        await context.send_activity(trace_activity)


ADAPTER.on_turn_error = on_error

# Create the Bot
BOT = EchoBot()

from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/api/messages', methods=['POST'])
async def messages():
    # if request.headers['Content-Type'] == 'application/json':
    #     activity = request.json()
    # else:
    #     return jsonify({'status': 'error', 'message': 'Unsupported Media Type'}), 415
    
    # print(request.json)
    # Set up logging
    logging.basicConfig(level=logging.INFO)

    # Log the request JSON
    logging.info(request.json)
    # logging.info(request.headers)
    # file = open("request.txt", "w")  
    # file.write(request.json)  
    # file.close()  

    activity = Activity().deserialize(request.json)

    auth_header = request.headers['Authorization'] if 'Authorization' in request.headers else ''
    claims = await decode_auth_header(ADAPTER, activity, auth_header, CONFIG.APP_ID)
    logging.info(claims)
    response = await ADAPTER.process_activity(activity, auth_header, BOT.on_message_activity)
    if response:
        return jsonify(response.body), response.status
    return '', 200

if __name__ == '__main__':
    try:
        app.run(host='localhost', port=CONFIG.PORT)
    except Exception as error:
        raise error

# Listen for incoming requests on /api/messages
# async def messages(req: Request) -> Response:
#     # Main bot message handler.
#     if "application/json" in req.headers["Content-Type"]:
#         body = await req.json()
#     else:
#         return Response(status=HTTPStatus.UNSUPPORTED_MEDIA_TYPE)

#     activity = Activity().deserialize(body)
#     auth_header = req.headers["Authorization"] if "Authorization" in req.headers else ""

#     response = await ADAPTER.process_activity(activity, auth_header, BOT.on_turn)
#     if response:
#         return json_response(data=response.body, status=response.status)
#     return Response(status=HTTPStatus.OK)


# APP = web.Application(middlewares=[aiohttp_error_middleware])
# APP.router.add_post("/api/messages", messages)

# if __name__ == "__main__":
#     try:
#         web.run_app(APP, host="localhost", port=CONFIG.PORT)
#     except Exception as error:
#         raise error
