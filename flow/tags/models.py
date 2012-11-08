"""
Shootout example app models: Ideas, Tags
"""
from sqlalchemy import Table
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy.orm import relation
from sqlalchemy.orm import backref
from sqlalchemy.orm import column_property
from sqlalchemy.types import Integer
from sqlalchemy.types import Unicode
from sqlalchemy.types import UnicodeText
from sqlalchemy.sql import func


from ..models import Base
from ..models import DBSession
from ..models import User


class Tag(Base):
    """
    Tag model.
    """
    __tablename__ = 'tags'
    tag_id = Column(Integer, primary_key=True)
    name = Column(Unicode(50), unique=True, index=True)

    def __init__(self, name):
        self.name = name

    @staticmethod
    def extract_tags(tags_string):
        tags = tags_string.replace(';', ' ').replace(',', ' ')
        tags = [tag.lower() for tag in tags.split()]
        tags = set(tags)

        return tags

    @classmethod
    def get_by_name(cls, tag_name):
        tag = DBSession.query(cls).filter(cls.name==tag_name)
        return tag.first()

    @classmethod
    def create_tags(cls, tags_string):
        tags_list = cls.extract_tags(tags_string)
        tags = []

        for tag_name in tags_list:
            tag = cls.get_by_name(tag_name)
            if not tag:
                tag = Tag(name=tag_name)
                DBSession.add(tag)
            tags.append(tag)

        return tags

    @classmethod
    def tag_counts(cls):
        query = DBSession.query(Tag.name, func.count('*'))
        return query.join('ideas').group_by(Tag.name)

