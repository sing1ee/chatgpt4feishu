from dotenv import load_dotenv
load_dotenv()

import openai

openai.debug = True
openai.log = "debug"


def chat_completion(*args, **kwargs):
    completion = openai.ChatCompletion.create(*args, **kwargs)
    return completion.choices[0].message.content

if __name__ == '__main__':
    kwargs = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {
            "role": "user",
            "content": "上海是一座"
            }
        ],
        "max_tokens": 3500,
        "temperature": 0.0
    }
    print(chat_completion(timeout=1, **kwargs))
    pass