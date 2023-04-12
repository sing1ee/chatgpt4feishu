# chatgpt4feishu
chatgpt robot for feishu

### Build
```shell
docker build -t feishu-robot .
```

### docker network
```shell
docker network create cc
```

### Run
```shell

docker run --rm --env-file .env -v /data/workspace/src/chatgpt4feishu:/home/app -p 6543:3456 --network cc  -it feishu-robot server.py
```

### Nginx 
```shell
        location /feishurobot/ {
            proxy_pass http://127.0.0.1:6543/;
            tcp_nodelay     on;
            proxy_read_timeout  7200;
            proxy_set_header Host            $host;
            proxy_set_header X-Real-IP       $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        }

```

### 设置飞书的订阅URL
```shell
 https://your_domain.com/feishurobot
```

### redis
```shell

docker run --name chat-redis --network cc -v /data/workspace/chat-redis-data/redis.conf:/etc/redis/redis.conf -v /data/workspace/chat-redis-data:/data -d redis redis-server /etc/redis/redis.conf



docker run -it --network cc --rm redis redis-cli -h chat-redis
```

### Message Queue
1. 有两个队列来存消息 chat_id_open_id_assistant 和 chat_id_open_id_user
- chat_id_open_id_assistant 私聊，或者群聊中，机器人回复某一用户
- chat_id_open_id_user 私聊，或者群聊中，用户说的话，在群聊中，包含 @机器人
2. chat_id_open_id_user 用户的消息保存在队列中。
3. 异步线程，处理 chat_id_open_id_user
- 当通过chatgpt获取到最新的回复，chat_id_open_id_user中没有新的消息，则私聊直接回复，群聊回复消息，然后机器人消息进入 chat_id_open_id_assistant
- 当通过chatgpt获取到最新的回复，chat_id_open_id_user中有新的消息，则私聊回复消息，群聊回复消息，然后机器人消息进入 chat_id_open_id_assistant
4. 调用chatgpt逻辑
- 获取历史的message，根据当前要回复的消息，找到这个消息以及之前的n条消息，包括 chat_id_open_id_assistant 和 chat_id_open_id_user，合并发给chatgpt。
- 如果通过prompt调整，则在这里处理。