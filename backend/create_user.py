from getpass import getpass

from app.database import SessionLocal
from app.models import User
from app.auth.security import hash_password


def create_user():
    db = SessionLocal()

    try:
        full_name = input("Enter full name: ").strip()
        email = input("Enter email: ").strip()
        role = input("Enter role (admin/hr/employee): ").strip().lower()
        password = getpass("Enter password: ")

        # Validate role
        allowed_roles = ["admin", "hr", "employee"]

        if role not in allowed_roles:
            print("Invalid role.")
            print("Allowed roles: admin, hr, employee")
            return

        # Validate password
        if len(password) < 8:
            print("Password must be at least 8 characters.")
            return

        # Check existing email
        existing_user = (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

        if existing_user:
            print("Email already exists.")
            return

        # Create user
        user = User(
            full_name=full_name,
            email=email,
            password_hash=hash_password(password),
            role=role,
            is_active=True,
        )

        db.add(user)
        db.commit()
        db.refresh(user)

        print()
        print("User created successfully.")
        print(f"User ID: {user.id}")
        print(f"Name: {user.full_name}")
        print(f"Email: {user.email}")
        print(f"Role: {user.role}")
        print(f"Active: {user.is_active}")

    finally:
        db.close()


if __name__ == "__main__":
    create_user()