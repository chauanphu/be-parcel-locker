from models import user, locker, order, parcel_type, parcel
from .__init__ import Base, engine

from models.user import Account
from auth.utils import bcrypt_context, authenticate_user
from decouple import config
from .session import session
ADMIN_USERNAME = config("ADMIN_USERNAME")
ADMIN_PASSWORD = config("ADMIN_PASSWORD")

def create_default_admin():
    with session as db:
    # Check if the admin user already exists
        admin = authenticate_user('admin@example.com', 'admin', db)
        # Check if the admin role already exists
        role_admin = db.query(user.Role).filter(user.Role.role_name == 'admin').first()
        if not role_admin:
            role_admin = user.Role()
            role_admin.role_name = 'admin'
            db.add(role_admin)
            db.commit()
            db.refresh(role_admin)
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
        admin_request.password = bcrypt_context.hash(ADMIN_PASSWORD)
        admin_request.role_id = role_admin.role_id
        db.add(admin_request)
        db.commit()
        print("Admin user created successfully.")