# coding: utf-8

import os

# path = u"BlockMov WEB端使用接口.md"
path = u"mobile_api.md"

with open(path) as fp:
    lines = fp.readlines()
    page = 0
    for line in lines:
        if line.startswith("#"):
            page += 1
            i = 0
            while line[i] == "#":
                i += 1
            t = ">" * (i - 2)
            s = "#" * i
            o = "{t}[{data}](##)\n".format(t=t, s=s, data=line[i + 1:-1])
            print o
    print page
