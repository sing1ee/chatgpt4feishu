#!/usr/bin/env python3.8
import json
import time
from api import message_api_client
from openai_client import chat_completion
from redis_client import users, get_user_msg_by_key, replied, is_replied
from utils import dict2obj

from concurrent.futures import ThreadPoolExecutor, wait
import threading

def gpt(key):
    print('%s %s' % (key, threading.current_thread().name))
    if key.startswith('group'):
        # load the latest msg
        msg = dict2obj(json.loads(get_user_msg_by_key(key, 0, 1)[0]))
        if not is_replied(key, msg.event.message.message_id):
            # print(json.dumps(obj2dict(msg.event.message)))
            txt = json.loads(msg.event.message.content)['text']
            for m in msg.event.message.mentions:
                txt = txt.replace(m.key, ' ')
            
            kwargs = {
                "model": "gpt-3.5-turbo",
                "messages": [
                    {
                    "role": "user",
                    "content": txt
                    }
                ],
                "max_tokens": 1000,
                "temperature": 0.0
            }
            content = chat_completion(**kwargs)
            message_api_client.reply(msg.event.message.message_id, 'text', json.dumps({'text':content}))
            replied(key, msg.event.message.message_id)
            pass
        return 2
    return 1
        


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=4) as pool:
            while True:
                keys = users()
                all_task = [pool.submit(gpt, k.decode('utf-8')) for k in keys]
                wait(all_task)
                # results = pool.map(gpt, map(lambda x : x.decode('utf-8'), keys))
                # for r in results:
                #     print('==', r)
                time.sleep(1)
