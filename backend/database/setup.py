# from models.user import User
from models.role import Role
from models.account import Account
from models.locker import *
from models.order import *
from models.parcel import *
from models.parcel_type import *

from auth.utils import authenticate_user, hash_password
from decouple import config
from .session import session
from .__init__ import Base

ADMIN_USERNAME = config("ADMIN_USERNAME")
ADMIN_PASSWORD = config("ADMIN_PASSWORD")

def create_roles():
    role_names = ["admin", "shipper", "customer"]
    with session as db:
        try:
            for role_name in role_names:
                role = db.query(Role).filter(Role.name == role_name).first()
                if not role:
                    role = Role(name=role_name)
                    db.add(role)
                    db.commit()
                    print(f"Role {role_name} created successfully.")
                else:
                    print(f"Role {role_name} already exists.")
        except Exception as e:
            db.rollback()
            print(f"Error creating roles: {str(e)}")
            raise

def create_default_admin():
    with session as db:
        try:
            admin = authenticate_user(ADMIN_USERNAME, ADMIN_PASSWORD, db)
            admin_role: Role = db.query(Role).filter(Role.name == "admin").first()
            if not admin_role:
                print("Admin role not found.")
                raise ValueError("Admin role not found.")
            if admin:
                print("Admin user already exists.")
                return
            if not ADMIN_USERNAME or not ADMIN_PASSWORD:
                print("Admin username and password not provided.")
                raise ValueError("Admin username and password not provided.")
            new_admin = Account(
                username=ADMIN_USERNAME,
                email="admin@example.com",
                password=hash_password(ADMIN_PASSWORD),
                role=admin_role.role_id,
            )
            db.add(new_admin)
            db.commit()
            
            print("Admin user created successfully.")
        except Exception as e:
            db.rollback()
            print(f"Error creating admin user: {str(e)}")
            raise
