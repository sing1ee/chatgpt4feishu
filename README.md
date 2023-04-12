# chatgpt4feishu
chatgpt robot for feishu

### Build
```shell
docker build -t feishu-robot .
```

### Run
```shell
docker run --rm --env-file .env -v /your_code_folder:/home/app -p 6543:3456  -it feishu-robot server.py
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