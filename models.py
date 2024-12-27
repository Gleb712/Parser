from sqlalchemy import Column, Integer, String, BaseRow
from database import Database


class Item(Database.Base):
    __tablename__ = "items"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    price = Column(Integer, nullable=False)
