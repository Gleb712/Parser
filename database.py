from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


class Database:
    # Настройка подключения к базе данных
    engine = create_engine("sqlite:///./items.db")
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()

    # Создание базы данных
    def create_db(self):
        self.Base.metadata.create_all(bind=self.engine)
