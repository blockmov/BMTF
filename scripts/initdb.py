from pprint import pprint

import models.all

from models import user
from models import role
from libs import utils

ROLE_ADMIN = "BM_ADMIN"
ROLE_AGENT = "BM_AGENT"
ROLE_FINANCE = "BM_FINANCE"
ROLE_CUSTOMER = "BM_CUSTOMER"

ROLE_SYSTEM = "BM_SYSTEM"

def init_database():
    print "=================== init database begin ==================="
    
    # create roles
    role.Role.add(name=ROLE_SYSTEM, description="System Role", access_urls="")
    role.Role.add(name=ROLE_ADMIN, description="Administrator Role", access_urls="")
    role.Role.add(name=ROLE_AGENT, description="Agent Role", access_urls="")
    role.Role.add(name=ROLE_FINANCE, description="Finance Role", access_urls="")
    role.Role.add(name=ROLE_CUSTOMER, description="Cusomer Role", access_urls="")
     
    admin_role = role.Role.fetch(ROLE_ADMIN)
    
     
    pprint ("====Roles")
    pprint (role.Role.list())
    pprint ("====Users")
    pprint (user.User.list())
    print "=================== init database end ==================="
    

if __name__ == "__main__":
    init_database()