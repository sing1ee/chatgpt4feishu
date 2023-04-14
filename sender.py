#!/usr/bin/env python3.8
import json
import time
from api import message_api_client
from openai_client import chat_completion
from redis_client import users, get_msg_by_key, replied, is_replied, role_assistant_key, role_user_key, last_reply_at, reply_cursor, push_assistant_msg_by_key
from utils import dict2obj

from concurrent.futures import ThreadPoolExecutor, wait
import threading

def gpt(key):
    print('%s %s' % (key, threading.current_thread().name))
    if key.startswith('group'):
        # load the latest msg
        msg = dict2obj(json.loads(get_msg_by_key(key, 0, 1)[0]))
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
    else:
        print('p2p')
        size = 10
        messages = []
        user_msg_list = get_msg_by_key(key, 0, size)
        assistan_msg_key = key.replace(role_user_key, role_assistant_key)
        assistan_msg_list = get_msg_by_key(assistan_msg_key, 0, size)
        last_replied_at = last_reply_at(key)
        print(last_replied_at)
        if not last_replied_at:
            last_replied_at = 0
        else:
            last_replied_at = int(last_replied_at.decode())
        print('last_at', last_replied_at)
        merged_list = []
        max_at = 0
        chat_id = ''
        if user_msg_list:
            at = dict2obj(json.loads(user_msg_list[0])).header.create_time
            print('check', at, last_replied_at)
            if int(at) <= last_replied_at:
                return
        for m in user_msg_list:
            user_msg = dict2obj(json.loads(m))
            chat_id = user_msg.event.message.chat_id
            send_at = int(user_msg.header.create_time)
            if send_at > max_at:
                max_at = send_at
            merged_list.append((send_at, 'user', json.loads(user_msg.event.message.content)['text'], user_msg.event.message.message_id))

        if not merged_list:
            return
        for m in assistan_msg_list:
            assistant_msg = dict2obj(json.loads(m))
            # if assistant_msg.at > last_replied_at:
            merged_list.append((int(assistant_msg.at), 'assistant', assistant_msg.text, ''))
        merged_list = sorted(merged_list, key=lambda s: s[0])
        for m in merged_list:
            data = {
                'role': m[1],
                'content': m[2]
            }
            print(json.dumps(data))
            messages.append(data)
        if merged_list[-1][1] == 'assistant':
            reply_cursor(key, merged_list[-1][0])
            return
        kwargs = {
                "model": "gpt-3.5-turbo",
                "messages": messages,
                "max_tokens": 1000,
                "temperature": 0.0
            }
        content = None
        try_num = 3
        while try_num > 0:
            try:
                content = chat_completion(timeout=1, **kwargs)
            except:
                messages = messages[:len(messages)/2]
                kwargs = {
                    "model": "gpt-3.5-turbo",
                    "messages": messages,
                    "max_tokens": 1000,
                    "temperature": 0.0
                }
                pass
        if not content:
            message_api_client.send('chat_id', chat_id, 'text', json.dumps({'text':content}))
            push_assistant_msg_by_key(assistan_msg_key, json.dumps({'at': int(round(time.time() * 1000)), 'text': '无法回答您的问题，可以试着问问别的。'}))
            reply_cursor(key, str(merged_list[-1][0]))
            return 0
        print(assistan_msg_key, json.dumps({'at': int(round(time.time() * 1000)), 'text': content}), merged_list[-1][0])
        latest_msg = dict2obj(json.loads(get_msg_by_key(key, 0, 1)[0]))
        if int(latest_msg.header.create_time) > max_at:
            # new msg comes
            message_api_client.reply(merged_list[-1][3], 'text', json.dumps({'text':content}))
            push_assistant_msg_by_key(assistan_msg_key, json.dumps({'at': int(round(time.time() * 1000)), 'text': content}))
            reply_cursor(key, str(merged_list[-1][0]))
        else:
            # no new msg
            message_api_client.send('chat_id', chat_id, 'text', json.dumps({'text':content}))
            push_assistant_msg_by_key(assistan_msg_key, json.dumps({'at': int(round(time.time() * 1000)), 'text': content}))
            reply_cursor(key, str(merged_list[-1][0]))
        pass
    return 1


if __name__ == "__main__":
    with ThreadPoolExecutor(max_workers=4) as pool:
            while True:
                keys = users()
                all_task = [pool.submit(gpt, k.decode('utf-8')) for k in keys]
                wait(all_task)
                time.sleep(1)