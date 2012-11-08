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

from ..tags.models import Tag

ideas_tags = Table('ideas_tags', Base.metadata,
    Column('idea_id', Integer, ForeignKey('ideas.idea_id')),
    Column('tag_id', Integer, ForeignKey('tags.tag_id'))
)




voted_users = Table('ideas_votes', Base.metadata,
    Column('idea_id', Integer, ForeignKey('ideas.idea_id')),
    Column('user_id', Integer, ForeignKey('users.user_id'))
)


class Idea(Base):
    __tablename__ = 'ideas'
    idea_id = Column(Integer, primary_key=True)
    target_id = Column(Integer, ForeignKey('ideas.idea_id'))
    comments = relation('Idea', cascade="delete",
        backref=backref('target', remote_side=idea_id))
    author_id = Column(Integer, ForeignKey('users.user_id'))
    author = relation(User, cascade="delete", backref='ideas')
    title = Column(UnicodeText)
    text = Column(UnicodeText)
    hits = Column(Integer, default=0)
    misses = Column(Integer, default=0)
    tags = relation(Tag, secondary=ideas_tags, backref='ideas')
    voted_users = relation(User, secondary=voted_users, lazy='dynamic',
        backref='voted_ideas')
    hit_percentage = func.coalesce(hits / (hits + misses) * 100, 0)

    hit_percentage = column_property(hit_percentage.label('hit_percentage'))

    total_votes = column_property((hits + misses).label('total_votes'))

    vote_differential = column_property(
        (hits - misses).label('vote_differential')
    )

    @classmethod
    def get_by_id(cls, idea_id):
        return DBSession.query(cls).filter(cls.idea_id==idea_id).first()

    @classmethod
    def get_by_tagname(cls, tag_name):
        return DBSession.query(Idea).filter(Idea.tags.any(name=tag_name))

    @classmethod
    def ideas_bunch(cls, order_by, how_many=10):
        q = DBSession.query(cls).join('author').filter(cls.target==None)
        return q.order_by(order_by)[:how_many]

    def user_voted(self, username):
        return bool(self.voted_users.filter_by(username=username).first())

