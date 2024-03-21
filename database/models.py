from sqlalchemy import Column, DateTime, Integer, LargeBinary, String, func
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class Product(Base):
    __tablename__ = 'product'

    id = Column(Integer, primary_key=True)
    article = Column(String(100))
    created_at = Column(DateTime, default=func.datetime('now', 'localtime'))
    photo = Column(String(10000))


class Article(Base):
    __tablename__ = 'article'

    id = Column(Integer, primary_key=True)
    article = Column(String(100), unique=True)