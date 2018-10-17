import hashlib
import os
import random
import string
import time
import uuid

import pycountry

from libs import phone_codes


def hash_password(password):
    return hashlib.sha1(password).hexdigest()


def gen_rand_num_str(length=6):
    digits = string.digits
    count = len(string.digits)
    s = []
    for i in xrange(length):
        index = random.randint(0, count - 1)
        s.append(digits[index])
    return "".join(s)


def gen_access_token():
    return hashlib.sha1(bytes('%s%s' % (os.urandom(16), time.time()))).hexdigest()


def gen_rand_avatar_name():
    return str(uuid.uuid4()).replace("-", "")[:12]


def all_countries():
    code_list = all_phone_code_list()
    result = {}
    for c in pycountry.countries:
        if c.alpha_2 not in code_list:
            phone_code = 0
        else:
            phone_code = code_list[c.alpha_2]
        uri = "/flags/" + c.alpha_2.lower() + ".gif"
        result[c.alpha_2] = {
            "alpha_2": c.alpha_2,
            "name": c.name,
            "numeric": c.numeric,
            "uri": uri,
            "phone_code": phone_code
        }
    return result


def all_currencies():
    all_currencies = [c for c in pycountry.currencies]
    result = {}
    for c in all_currencies:
        result[c.alpha_3] = c
    return result


def all_phone_code_list():
    code_list = {}
    for c in phone_codes.codes_list:
        code_list[c[1]] = c[0]
    return code_list


def find_country_by_name(country_name):
    countries = all_countries()
    for c in countries:
        if country_name == countries[c]["name"]:
            return countries[c]
    return None


def find_country_by_code(country_code):
    countries = all_countries()
    for c in countries:
        if country_code == countries[c]["alpha_2"]:
            return countries[c]
    return None


from models import fee_method
from models import fee_detail


def fee_calc(src_country, dst_country, fee_method_type, amount):
    amount = float(amount)
    _method = fee_method.FeeMethod.on_find_fee_method_by_country(src_country, dst_country, fee_method_type)
    if not _method:
        return -1, fee_method_type, 0
    if not _method.fee_details:
        return -1, fee_method_type, 0
    return 0, fee_method_type, 10.00
