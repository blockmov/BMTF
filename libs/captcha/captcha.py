#!/usr/bin/env python
# encoding: utf-8
from cStringIO import StringIO
from random import randint, choice
from string import printable

from PIL import Image, ImageDraw, ImageFont


def gen_captcha(width, height):
    # 设置选用的字体
    font_path = "utils/captcha/font/arial.ttf"
    font_color = (randint(150, 200), randint(0, 150), randint(0, 150))
    line_color = (randint(0, 150), randint(0, 150), randint(150, 200))
    point_color = (randint(0, 150), randint(50, 150), randint(150, 200))

    # 设置验证码的宽与高
    image = Image.new("RGB", (width, height), (200, 200, 200))
    font = ImageFont.truetype(font_path, height - 10)
    draw = ImageDraw.Draw(image)

    # 生成验证码
    text = "".join([choice(printable[:62]) for i in xrange(4)])
    font_width, font_height = font.getsize(text)
    # 把验证码写在画布上
    draw.text((10, 10), text, font=font, fill=font_color)
    # 绘制干扰线
    for i in xrange(0, 5):
        draw.line(((randint(0, width), randint(0, height)),
                   (randint(0, width), randint(0, height))),
                  fill=line_color, width=2)

    # 绘制点
    for i in xrange(randint(100, 1000)):
        draw.point((randint(0, width), randint(0, height)), fill=point_color)
    # 输出
    out = StringIO()
    image.save(out, format='gif')
    content = out.getvalue()
    out.close()
    return text, content
