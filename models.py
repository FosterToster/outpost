from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, Enum as DBEnum
from sqlalchemy.orm import relationship
from sqlalchemy.inspection import inspect
from sqlalchemy import Column
from enum import Enum

class Gender(Enum):
    MALE = 'MALE'
    FEMALE = "FEMALE"

class Idiots(Enum):
    NONE = "NONE"
    PIZZA = "PIZZA"

from orm import DeclarativeBase

class IdDeletable:
    id = Column(Integer, primary_key=True, nullable=False)
    deleted = Column(Boolean, nullable=False, default=False)

class Phone(IdDeletable, DeclarativeBase):
    __tablename__ = 'phones'

    user_id = Column(Integer, ForeignKey('users.id'))
    user = relationship('User', back_populates='phones', uselist=False)

    number = Column(String(15), nullable=False)

    

class User(IdDeletable, DeclarativeBase):
    __tablename__ = "users"
    phones = relationship(Phone, back_populates='user')

    name = Column(String(100), nullable=False)
    hash = Column(String, nullable=False)
    gender = Column(DBEnum(Gender, Idiots))


# print(User.__table__.columns)
# print(User.__table__.foreign_keys)
# print(User.__table__.__dict__)
# print('\n'.join(f'{k}: {v}' for k,v in inspect(Phone).__dict__.items()))
# print(inspect(User).columns)
# print(inspect(User).foreign_keys)
# print(*[x for x in inspect(User).relationships])
# print(inspect(User))