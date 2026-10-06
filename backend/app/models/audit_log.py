from datetime import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from app.database import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, nullable=True, index=True)

    user_email = Column(String(255), nullable=True)

    action = Column(String(100), nullable=False)

    entity = Column(String(100), nullable=True)

    entity_id = Column(Integer, nullable=True)

    description = Column(Text, nullable=False)

    timestamp = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
    )

    ip_address = Column(String(100), nullable=True)