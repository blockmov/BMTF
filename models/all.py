from models import BaseModel
from models import DB

from models import role
from models import action

from models import company
from models import user
from models import company_card
from models import fee_method
from models import fee_detail
from models import user_message

from models import customer
from models import customer_wallet
from models import customer_card
from models import customer_contact
from models import customer_message
from models import customer_operation



from models import deposit
from models import payment
from models import transfer
from models import withdraw
from models import withdraw_rule

from models import zone



BaseModel.metadata.create_all(DB)
