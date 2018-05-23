#!/usr/bin/env python
# __author__ = lvhuiyang

import base64
from io import BytesIO
from uuid import uuid4

from PIL import Image
from flask import Flask, request
from celery import Celery
from redis import ConnectionPool, Redis

app = Flask(__name__)
app.config['CELERY_BROKER_URL'] = 'redis://localhost:6379'

celery = Celery(app.name, broker=app.config['CELERY_BROKER_URL'])
celery.conf.update(app.config)

pool = ConnectionPool(host='localhost', port=6379, decode_responses=True)
client = Redis(connection_pool=pool)

ACCESS_TOKEN = ""


def make_uuid():
    return str(uuid4()).replace('-', '')


@celery.task
def handler(uuid, text):
    """
    图片处理函数
    :param uuid: 唯一id
    :param text: 输入的文字
    :return:
    """
    output = BytesIO()
    image = Image.open("/Users/lvhuiyang/Pictures/blog/0826/路由表举例.jpg")
    # image = Image.open("/Users/lvhuiyang/Desktop/demo.jpeg")
    image.save(output, format="JPEG")

    im_data = output.getvalue()
    # data_url = 'data:image/jpg;base64,' + str(base64.b64encode(im_data))
    client.set(uuid, base64.b64encode(im_data))
    return True


@app.route("/", methods=['POST'])
def index():
    text = request.form.get('text')
    token = request.form.get('token')
    if text and token == "temp_token":
        text_uuid = client.get(text)
        if text_uuid:
            return "生成地址: {}meme/{}/".format(request.url, text_uuid)
        else:
            new_uuid = make_uuid()
            client.set(text, new_uuid)
            handler(new_uuid, text)
            return "生成地址: {}meme/{}/".format(request.url, new_uuid)
    return "参数不正确"


@app.route("/meme/<string:key>/", methods=['GET'])
def meme(key):
    value = client.get(key)

    if value is None:
        return "访问地址不存在或者已经过期."
    elif value == "0":
        return "当你看到当前页面的时候说明图片正在生成，请等待几秒尝试刷新."
    else:
        img_value = "data:image/jpeg;base64," + value
        print(img_value)
        return "<img src={}/>".format(img_value)


if __name__ == '__main__':
    app.run(debug=True)
