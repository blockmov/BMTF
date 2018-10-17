# coding: utf-8
import os

# 账户类型
ACCOUNT_TYPE_PERSON = 'P'
ACCOUNT_TYPE_ENTERPRISE = 'E'

# BM公司交易状态
BM_GROUP_STATUS_OPEN = "open"
BM_GROUP_STATUS_CLOSE = "close"

# BM公司员工状态
BM_USER_STATUS_ENABLE = "enable"
BM_USER_STATUS_DISABLE = "disable"

# token过期时间
VERIFY_TOKEN_TIMEOUT = 600

# 默认角色
ROLE_SYSTEM = "SYSTEM"
ROLE_ADMIN = "ADMIN"
ROLE_AGENT = "AGENT"
ROLE_FINANCE = "FINANCE"
DEFAULT_ROLES = [ROLE_SYSTEM, ROLE_ADMIN, ROLE_AGENT, ROLE_FINANCE]

# 默认公司
GROUP_CBS = "CBS"
DEFAULT_GROUPS = [GROUP_CBS]

# 默认用户
DEFAULT_USERS = [USER_ADMIN, USER_AGENT, USER_FINANCE]

# 银行交易状态
BANK_STATUS_OPEN = "open"
BANK_STATUS_CLOSE = "close"

# 账户审核状态
AUDIT_STATUS_PASS = "pass"
AUDIT_STATUS_NOT_PASS = "not_pass"
AUDIT_STATUS_PENDING = "pending"


# 证件图片保存路径
IDENTITY_FILE_PATH = os.path.join("data", "identity")

# 头像图片保存路径
AVATAR_FILE_PATH = os.path.join("data", "avatar")

# 充值图片保存路径
DEPOSIT_FILE_PATH = os.path.join("data", "deposit")

# 提现图片保存路径
WITHDRAW_FILE_PATH = os.path.join("data", "withdraw")

# 转账图片保存路径
TRANSFER_FILE_PATH = os.path.join("data", "transfer")

# 国旗资源
FLAGS_FILE_PATH = os.path.join("resource", "flags")