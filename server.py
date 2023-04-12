#!/usr/bin/env python3.8
from dotenv import load_dotenv, find_dotenv
load_dotenv(find_dotenv())

import json
import os
import logging
import requests
import time
from api import MessageApiClient
from event import MessageReceiveEvent, UrlVerificationEvent, MessageReadEvent, EventManager
from flask import Flask, jsonify
from openai_client import chat_completion
from redis_client import push_user_msg, users, get_user_msg_by_key, replied, is_replied
from utils import obj2dict, dict2obj

from concurrent.futures import ThreadPoolExecutor
import threading


# load env parameters form file named .env


app = Flask(__name__)

# load from env
APP_ID = os.getenv("APP_ID")
APP_SECRET = os.getenv("APP_SECRET")
VERIFICATION_TOKEN = os.getenv("VERIFICATION_TOKEN")
ENCRYPT_KEY = os.getenv("ENCRYPT_KEY")
LARK_HOST = os.getenv("LARK_HOST")

# init service
message_api_client = MessageApiClient(APP_ID, APP_SECRET, LARK_HOST)
event_manager = EventManager()

@event_manager.register("url_verification")
def request_url_verify_handler(req_data: UrlVerificationEvent):
    # url verification, just need return challenge
    if req_data.event.token != VERIFICATION_TOKEN:
        raise Exception("VERIFICATION_TOKEN is invalid")
    return jsonify({"challenge": req_data.event.challenge})

@event_manager.register("im.message.message_read_v1")
def request_read_handler(req_data: MessageReadEvent):
    return jsonify()


@event_manager.register("im.message.receive_v1")
def message_receive_event_handler(req_data: MessageReceiveEvent):
    sender_id = req_data.event.sender.sender_id
    message = req_data.event.message
    msg = json.dumps(obj2dict(req_data))
    print(msg)
    if message.message_type != "text":
        logging.warning("Other types of messages have not been processed yet")
        return jsonify()
        # get open_id and text_content
    # ou_3f08bfcc9b16f3146507814b9ea5245c
    if message.chat_type == 'group':
        if hasattr(message, 'mentions') and message.mentions:
            for m in message.mentions:
                if m.id.open_id == 'ou_3f08bfcc9b16f3146507814b9ea5245c':
                    push_user_msg(message.chat_id, sender_id.open_id, message.chat_type, msg)
                    break
    else:
        push_user_msg(message.chat_id, sender_id.open_id, message.chat_type, msg)
    # if message.chat_type == 'group':
    #     message_api_client.send('chat_id', message.chat_id, 'text', json.dumps({'text':'echo'}))
    return jsonify()


@app.errorhandler
def msg_error_handler(ex):
    logging.error(ex)
    response = jsonify(message=str(ex))
    response.status_code = (
        ex.response.status_code if isinstance(ex, requests.HTTPError) else 500
    )
    return response


@app.route("/", methods=["POST"])
def callback_event_handler():
    # init callback instance and handle
    event_handler, event = event_manager.get_handler_with_event(VERIFICATION_TOKEN, ENCRYPT_KEY)
    if not event_handler or not event:
        return jsonify()
    return event_handler(event)


def gpt(key):
    if key.startswith('group'):
        # load the latest msg
        msg = dict2obj(json.loads(get_user_msg_by_key(key, 0, 1)[0]))
        if not is_replied(key, msg.event.message.message_id):
            print(json.dumps(obj2dict(msg.event.message)))
            txt = json.loads(msg.event.message.content)['text']
            for m in msg.event.message.mentions:
                txt = txt.replace(m.key, ' ')
            print(txt)
            # content = chat_completion(kwargs = {
            #     "model": "gpt-3.5-turbo",
            #     "messages": [
            #         {
            #         "role": "user",
            #         "content": 
            #         }
            #     ],
            #     "max_tokens": 200,
            #     "temperature": 0.0
            # })

            pass
    return key

class LoopWorker (threading.Thread):

    def __init__(self, name):
        threading.Thread.__init__(self)
        self.name = name

    def run(self):
        while True:
            keys = users()
            with ThreadPoolExecutor(max_workers=min(len(keys), (os.cpu_count() or 1) + 4)) as pool:
                results = pool.map(gpt, map(lambda x : x.decode('utf-8'), keys))
                for r in results:
                    print(r)
            time.sleep(1)


if __name__ == "__main__":
    LoopWorker('loop_worker').start()
    app.run(host="0.0.0.0", port=3456, debug=True)
