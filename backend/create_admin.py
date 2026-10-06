from getpass import getpass

from app.database import SessionLocal
from app.models.user import User
from app.auth.security import hash_password


def create_admin():
    db = SessionLocal()

    try:
        email = input("Enter admin email: ").strip()
        full_name = input("Enter admin full name: ").strip()
        password = getpass("Enter admin password: ")

        if len(password) < 8:
            print("Password must be at least 8 characters.")
            return

        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user:
            existing_user.full_name = full_name
            existing_user.password_hash = hash_password(password)
            existing_user.role = "admin"
            existing_user.is_active = True

            db.commit()

            print("Existing user promoted to Admin successfully.")
            print(f"Email: {existing_user.email}")
            print("Role: admin")
            return

        admin = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role="admin",
            is_active=True,
        )

        db.add(admin)
        db.commit()
        db.refresh(admin)

        print("Admin account created successfully.")
        print(f"Admin ID: {admin.id}")
        print(f"Email: {admin.email}")
        print("Role: admin")

    finally:
        db.close()


if __name__ == "__main__":
    create_admin()