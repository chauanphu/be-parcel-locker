from models import user, locker, order, parcel_type, parcel
from .__init__ import Base, engine

from models.user import User
from auth.utils import bcrypt_context, authenticate_user
from database.session import get_db
from decouple import config
from .session import session
ADMIN_USERNAME = config("ADMIN_USERNAME")
ADMIN_PASSWORD = config("ADMIN_PASSWORD")

Base.metadata.create_all(bind=engine)
print("Database tables created")


def create_default_admin():
    with session as db:
    # Check if the admin user already exists
        admin = authenticate_user('admin@example.com', 'admin', db)
        if admin:
            print("Admin user already exists.")
            return
        if not ADMIN_USERNAME or not ADMIN_PASSWORD:
            print("Admin username and password not provided.")
            raise ValueError("Admin username and password not provided.")
        # # If not, create a new admin user
        admin_request = User()
        admin_request.username = ADMIN_USERNAME
        admin_request.email = "admin@example.com"
        admin_request.name = "Admin"
        admin_request.address = ""
        admin_request.phone = ""
        admin_request.password = bcrypt_context.hash(ADMIN_PASSWORD)
        db.add(admin_request)
        db.commit()
        print("Admin user created successfully.")

# Call the function during application startup
create_default_admin()