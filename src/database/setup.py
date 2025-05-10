# from models.user import User
from models.role import Role
from models.account import Account
from models.profile import Profile
from models.locker import *
from models.recipient import *
from models.order import *
from models.parcel import *
from models.parcel_type import *
from models.profile import *
from models.shipper import *

from auth.utils import authenticate_user, hash_password
from decouple import config
from .session import session
from .__init__ import Base

ADMIN_USERNAME = config("ADMIN_USERNAME")
ADMIN_PASSWORD = config("ADMIN_PASSWORD")

def create_default_admin():
    with session as db:
    # Check if the admin user already exists
        admin = authenticate_user(ADMIN_USERNAME, ADMIN_PASSWORD, db)
        if admin:
            print("Admin user already exists.")
            return
        if not ADMIN_USERNAME or not ADMIN_PASSWORD:
            print("Admin username and password not provided.")
            raise ValueError("Admin username and password not provided.")
        # # If not, create a new admin user
        admin_request = Account()
        admin_request.username = ADMIN_USERNAME
        admin_request.email = "admin@example.com"
        admin_request.password = hash_password(ADMIN_PASSWORD)
        admin_request.role = 1
        db.add(admin_request)
        db.commit()
        
        admin_request_2 = Profile()
        admin_request_2.name = "Admin"
        admin_request_2.address = ""
        admin_request_2.phone = ""
        db.add(admin_request_2)
        db.commit()
        
        print("Admin user created successfully.")
