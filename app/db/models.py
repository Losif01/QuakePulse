from sqlalchemy import Column, Integer, Float, String, DateTime, UniqueConstraint
from app.core.database import Base

class Earthquake(Base):
    __tablename__ = "earthquakes"

    id = Column(Integer, primary_key=True, index=True)
    time = Column(DateTime(timezone=True), nullable=False, index=True)
    magnitude = Column(Float, nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    depth = Column(Float, nullable=False)
    place = Column(String, nullable=True)

    __table_args__ = (
        UniqueConstraint('time', 'latitude', 'longitude', name='_time_location_uc'),
    )
