# coding: utf-8
import datetime
import uuid
import decimal

import const
from libs import utils
from models.all import company
from models.all import company_card
from models.all import customer
from models.all import customer_card
from models.all import customer_contact
from models.all import customer_wallet
from models.all import customer_message
from models.all import fee_detail
from models.all import fee_method
from models.all import role
from models.all import user


def init_database():
    password = utils.hash_password("123456")
    print "=================== Init database begin ==================="

    # 1. 创建角色
    role.Role.on_add_new_role(role_name=const.ROLE_SYSTEM, description="System Role", access_urls="")
    role.Role.on_add_new_role(role_name=const.ROLE_ADMIN, description="Administrator Role", access_urls="")
    role.Role.on_add_new_role(role_name=const.ROLE_AGENT, description="Agent Role", access_urls="")
    role.Role.on_add_new_role(role_name=const.ROLE_FINANCE, description="Finance Role", access_urls="")

    system_role = role.Role.on_find_role_by_name(role_name=const.ROLE_SYSTEM)
    admin_role = role.Role.on_find_role_by_name(role_name=const.ROLE_ADMIN)
    agent_role = role.Role.on_find_role_by_name(role_name=const.ROLE_AGENT)
    finance_role = role.Role.on_find_role_by_name(role_name=const.ROLE_FINANCE)
    if None in (admin_role, agent_role, finance_role, system_role):
        print "init database failed: can't create default roles"
        return

    # 2. 创建公司
    c_china = utils.find_country_by_name("China")
    c_hongkong = utils.find_country_by_name("Hong Kong")

    company.Company.on_add_new_company(u"BlockMov (China)", c_china["alpha_2"], u"Shanghai", u"深圳怡景大厦-东座32号",
                                       u"Asia/Shanghai",
                                       u"USD", u"")
    company.Company.on_add_new_company(u"BlockMov (Hong Kong)", c_hongkong["alpha_2"], u"Hong Kong",
                                       u"34 Jordan Rd, Yau Ma Tei, 香港",
                                       u"Asia/Hong_Kong", u"USD", u"")

    china_com = company.Company.on_find_company_by_name(u"BlockMov (China)")
    hk_com = company.Company.on_find_company_by_name(u"BlockMov (Hong Kong)")

    # 设置为正常营业状态
    company.Company.on_set_state(china_com.company_id, "00")
    company.Company.on_set_state(hk_com.company_id, "00")

    # 设置营业时间
    opening_hours = datetime.time(9, 0)
    closing_hours = datetime.time(9, 0)
    company.Company.on_set_business_hours(china_com.company_id, opening_hours, closing_hours)
    company.Company.on_set_business_hours(hk_com.company_id, opening_hours, closing_hours)

    # 添加公司银行卡
    card_name = u"BlockMov"
    card_number = u"6229-8888-8888-8888"
    bank_swift_code = u"HSMBHKHHXXX"
    bank_name = u"HSBC GLOBAL ASSET MANAGEMENT HOLDINGS (BAHAMAS) LIMITED"
    # bank_country_code = c_hongkong["alpha_2"]
    # bank_city = "Hong Kong"
    bank_address = u"HSBC MAIN BUILDING FLOOR 22 1 QUEEN'S ROAD CENTRAL, 香港旺角弥敦道673号"
    currency = u"USD"
    amount = decimal.Decimal("9867100889892998982.00")

    company_card.BankCard.on_add_new_bank_card(hk_com.company_id, card_name, card_number, bank_swift_code, bank_name,
                                               bank_address, currency, amount)

    # 3. 创建BM用户
    user.User.on_add_new_user("system", "system@localhost.com", password, "138999999999", "Chinese",
                              system_role.role_id,
                              hk_com.company_id)
    user.User.on_add_new_user("admin", "admin@localhost.com", password, "138999999999", "Chinese", admin_role.role_id,
                              hk_com.company_id)
    user.User.on_add_new_user("finance", "finance@localhost.com", password, "138999999999", "Chinese",
                              finance_role.role_id,
                              hk_com.company_id)
    user.User.on_add_new_user("agent", "agent@localhost.com", password, "138999999999", "Chinese", agent_role.role_id,
                              hk_com.company_id)

    user.User.on_add_new_user("admin_hk", "adminhk@localhost.com", password, "138999999999", "English",
                              admin_role.role_id, hk_com.company_id)
    user.User.on_add_new_user("finance_hk", "financehk@localhost.com", password, "138999999999", "English",
                              finance_role.role_id, hk_com.company_id)
    user.User.on_add_new_user("agent_hk", "agenthk@localhost.com", password, "138999999999", "English",
                              agent_role.role_id, hk_com.company_id)

    # 8. 添加收费标准
    fee_method_id_list = []
    src_time_begin = datetime.datetime.time(datetime.datetime(2018, 9, 9, hour=9, minute=0))
    src_time_end = datetime.datetime.time(datetime.datetime(2018, 9, 9, hour=18, minute=0))
    dst_time_begin = datetime.datetime.time(datetime.datetime(2018, 9, 9, hour=11, minute=0))
    dst_time_end = datetime.datetime.time(datetime.datetime(2018, 9, 9, hour=15, minute=0))

    for c_name in ("Hong Kong", "Congo", "United States", "United Kingdom", "Germany", "United Arab Emirates"):
        c_country = utils.find_country_by_name(c_name)
        m1 = fee_method.FeeMethod.on_add_new_fee_method(hk_com.company_id, "00", hk_com.country, c_country["alpha_2"],
                                                        "1,2,3,4,5", src_time_begin, src_time_end, dst_time_begin,
                                                        dst_time_end, 30, 240)
        fee_method_id_list.append(m1.fee_method_id)

    for m in fee_method_id_list:
        fee_detail.FeeDetail.on_add_new_fee_detail(m, 0.0, 100000.00, 0.03, 100, 5000000.0)
        fee_detail.FeeDetail.on_add_new_fee_detail(m, 100000.0, 200000.00, 0.03, 100, 5000000.0)
        fee_detail.FeeDetail.on_add_new_fee_detail(m, 200000.0, 300000.00, 0.03, 100, 5000000.0)
        fee_detail.FeeDetail.on_add_new_fee_detail(m, 300000.0, 400000.00, 0.03, 100, 5000000.0)
        fee_detail.FeeDetail.on_add_new_fee_detail(m, 400000.0, 500000.00, 0.03, 100, 5000000.0)
        fee_detail.FeeDetail.on_add_new_fee_detail(m, 500000.0, 1000000.00, 0.03, 100, 5000000.0)
        fee_detail.FeeDetail.on_add_new_fee_detail(m, 1000000.0, 20000000.00, 0.03, 100, 5000000.0)

    # 4. 创建客户
    customer.Customer.on_add_new_customer(hk_com.company_id, "00", "demo@cbs.com", password)

    demo = customer.Customer.on_find_customer_by_email("demo@cbs.com")

    # 5. 创建钱包
    for u in (demo,):
        wallet_name = str(uuid.uuid4())
        if not u.wallet:
            wallet = customer_wallet.Wallet.on_add_new_wallet(u.cust_id, wallet_name)
            print "create new wallet: %s" % (wallet.to_dict())

    demo = customer.Customer.on_find_customer_by_email("demo@cbs.com")
    # 6. 创建银行卡
    for u in (demo,):
        wallet_id = u.wallet.wallet_id
        bank_card_name = u"Demo Account"
        bank_card_number = u"6229-4688-8888-8888"
        bank_swift_code = u"HSMBHKHHXXX"
        bank_name = u"HSBC GLOBAL ASSET MANAGEMENT HOLDINGS (BAHAMAS) LIMITED"
        bank_country_code = c_hongkong["alpha_2"]
        bank_city = "Hong Kong"
        bank_address = u"HSBC MAIN BUILDING FLOOR 22 1 QUEEN'S ROAD CENTRAL, 香港旺角弥敦道673号"
        customer_card.Card.on_add_new_card(wallet_id, bank_card_name, bank_card_number, bank_swift_code, bank_name,
                                           bank_country_code, bank_city, bank_address)

    # 7. 添加联系人
    for u in (demo,):
        contact_name = u"Li Lei"
        bank_card_name = u"Li Lei"
        bank_card_number = u"6225-0000-0000-0000"
        bank_swift_code = u"SCSEHKH1XXX"
        bank_name = u"Standard Chartered Bank"
        bank_country_code = c_hongkong["alpha_2"]
        bank_city = u"Hong Kong"
        bank_address = u"BANK OF CHINA TOWER FLOOR 23 1 GARDEN ROAD CENTRAL HONG KONG"
        _contact = customer_contact.Contact.on_add_new_contact(u.cust_id, contact_name, bank_card_name,
                                                               bank_card_number,
                                                               bank_swift_code, bank_name, bank_country_code, bank_city,
                                                               bank_address)

    # 测试消息历史
    for u in (demo,):
        for i in xrange(10):
            customer_message.CustomerMessage.on_add_new_message(message_type="deposit", message_content=u"您充值了$5000USD",
                                                                cust_id=u.cust_id)
            customer_message.CustomerMessage.on_add_new_message(message_type="withdraw",
                                                                message_content=u"您提现了$5000USD",
                                                                cust_id=u.cust_id)
            customer_message.CustomerMessage.on_add_new_message(message_type="transfer", message_content=u"转账成功",
                                                                cust_id=u.cust_id)
            customer_message.CustomerMessage.on_add_new_message(message_type="payment",
                                                                message_content=u"您在京东商场消费了3000元",
                                                                cust_id=u.cust_id)
            customer_message.CustomerMessage.on_add_new_message(message_type="notify", message_content=u"此处是通知",
                                                                cust_id=u.cust_id)

    print "=================== Init database end ==================="


if __name__ == "__main__":
    init_database()
    demo = customer.Customer.on_find_customer_by_email("demo@cbs.com")
    if demo.wallet:
        wallet_id = demo.wallet.wallet_id
        customer_wallet.Wallet.on_set_amount(wallet_id, 2800873333333.999)
        customer_wallet.Wallet.on_set_cash_amount(wallet_id, 12999988723.000)
        customer_wallet.Wallet.on_set_uncash_amount(wallet_id, 1289888989.100)
        customer_wallet.Wallet.on_set_freeze_cash_amount(wallet_id, 823434343.892)
        customer_wallet.Wallet.on_set_freeze_uncash_amount(wallet_id, 92.89)
