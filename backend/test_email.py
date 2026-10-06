import asyncio

from app.services.email_service import send_email


async def main():
    await send_email(
        "narukullaabhilash20@gmail.com",
        "HRMS Email Test",
        "This is a test email from the HRMS application."
    )

    print("Email sent successfully!")


if __name__ == "__main__":
    asyncio.run(main())