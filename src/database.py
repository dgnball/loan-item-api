from sqlalchemy import Column, ForeignKey, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
import os
from time import sleep

Base = declarative_base()


class User(Base):
    __tablename__ = "user"
    username = Column(String, primary_key=True)
    hashed_password = Column(String)
    role = Column(String)
    phone = Column(String)


class LoanItem(Base):
    __tablename__ = "LoanItem"
    id = Column(String, primary_key=True)
    description = Column(String)
    loanedto = Column(String, ForeignKey("user.username"))


sql_connect = "sqlite:///:memory:"  # Unit test only. For some reason this fails when handling real http requests.
# sql_connect = 'postgresql://postgres:mysecretpassword@localhost/template1'
if "DATABASE_URL" in os.environ:
    sql_connect = os.environ["DATABASE_URL"]
    sleep(2)  # Give external database time to accept connections

# engine = create_engine(sql_connect, echo=True)
engine = create_engine(sql_connect)
Base.metadata.create_all(engine)
Base.metadata.bind = engine
DBSession = sessionmaker(bind=engine)


# For testing
def get_db_session():
    return DBSession()


# For testing
def recreate_db():
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
