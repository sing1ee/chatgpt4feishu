import os
import redis

role_assistant_key = "_assistant"
role_user_key = "_user"

__poll = redis.ConnectionPool(host='chat-redis', db=0, password=os.getenv('REDIS_PWD'), port=6379)
__rclient = redis.Redis(connection_pool=__poll)
print('redis init ', __rclient.get('REDIS_PWD'))

def __user_key(chat_id, user_id):
    return '%s_%s_%s' % (chat_id, user_id, role_user_key)

def __assistant_key(chat_id, user_id):
    return '%s_%s_%s' % (chat_id, user_id, role_assistant_key)

def push_user_msg(chat_id, user_id, msg):
    __rclient.lpush(__user_key(chat_id, user_id), msg)

def push_assistant_msg(chat_id, user_id, msg):
    __rclient.lpush(__assistant_key(chat_id, user_id), msg)

def get_user_msg(chat_id, user_id, start, end):
    return __rclient.lrange(__user_key(chat_id, user_id), start, end)

def get_assistant_msg(chat_id, user_id, start, end):
    return __rclient.lrange(__assistant_key(chat_id, user_id), start, end)
