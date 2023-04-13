import os
import redis

role_assistant_key = "_assistant"
role_user_key = "_user"

__poll = redis.ConnectionPool(host='chat-redis', db=0, password=os.getenv('REDIS_PWD'), port=6379)
__rclient = redis.Redis(connection_pool=__poll)
print('redis init ', __rclient.get('__version__'))

def __user_key(chat_id, user_id, chat_type):
    return '%s_%s_%s_%s' % (chat_type, chat_id, user_id, role_user_key)

def __assistant_key(chat_id, user_id, chat_type):
    return '%s_%s_%s_%s' % (chat_type, chat_id, user_id, role_assistant_key)

def push_user_msg(chat_id, user_id, chat_type, msg):
    __rclient.lpush(__user_key(chat_id, user_id, chat_type), msg)

def push_assistant_msg(chat_id, user_id, chat_type, msg):
    __rclient.lpush(__assistant_key(chat_id, user_id, chat_type), msg)

def push_assistant_msg_by_key(key, msg):
    __rclient.lpush(key, msg)

def get_user_msg(chat_id, user_id, chat_type, start, end):
    return __rclient.lrange(__user_key(chat_id, user_id, chat_type), start, end)

def get_msg_by_key(key, start, end):
    return __rclient.lrange(key, start, end)

def get_assistant_msg(chat_id, user_id, chat_type, start, end):
    return __rclient.lrange(__assistant_key(chat_id, user_id, chat_type), start, end)

def users():
    return __rclient.keys('*_%s' % role_user_key)

def replied(key, message_id, ts=1):
    __rclient.hset('%s_replied' % key, message_id, ts)

# get ts
def replied_at(key, message_id):
    return __rclient.hget('%s_replied' % key, message_id)

def is_replied(key, message_id):
    return __rclient.hget('%s_replied' % key, message_id) is not None

def reply_cursor(key, ts):
    __rclient.set('%s_cursor' % key, ts)

def last_reply_at(key):
    return __rclient.get('%s_cursor' % key)