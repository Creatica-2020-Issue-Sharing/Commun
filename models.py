from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()

class Community(Base):
    __tablename__ = 'community'
    id = Column(UUID(as_uuid=True), primary_key=True)
    name = Column(String)

class User(Base):
    __tablename__ = 'users'
    id = Column(UUID(as_uuid=True), primary_key=True)
    username = Column(String)
    password = Column(String)
    email = Column(String)
    datecreated = Column(DateTime)
    profilepic = Column(String)

class Issue(Base):
    __tablename__ = 'issue'
    id = Column(UUID(as_uuid=True), primary_key=True)
    title = Column(String)
    #info = Column(String)
    dateof = Column(DateTime)
    communityid = Column(UUID(as_uuid=True))
    about = Column(String)
    imagepath = Column(String)

class Link(Base):
    __tablename__ = "link"
    id = Column(UUID(as_uuid=True), primary_key=True)
    issueid = Column(UUID(as_uuid=True))
    title = Column(String)
    ref = Column(String)

class Discussion(Base):
    __tablename__ = 'discussion'
    id = Column(UUID(as_uuid=True), primary_key=True)
    dateposted = Column(DateTime)
    authorid = Column(UUID(as_uuid=True))
    content = Column(String)
    imageupload = Column(String)