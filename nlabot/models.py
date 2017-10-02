#   encoding: utf-8
#   models.py

from datetime import datetime
from sqlalchemy import Column, DateTime, Integer, String, ForeignKey, \
        create_engine
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.orm import scoped_session, sessionmaker, relationship
from sqlalchemy import text


def connect_database(uri):
    sess = scoped_session(sessionmaker(
        autocommit=False,
        autoflush=False,
        bind=create_engine(uri, pool_recycle=3600)))

    return sess


@as_declarative()
class Base(object):

    pass


class User(Base):

    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    username = Column(String(64), nullable=True)
    first_name = Column(String(64), nullable=True)
    last_name = Column(String(64), nullable=True)
    last_seen_at = Column(DateTime, default=datetime.now, nullable=False)
    # TODO add server_default with timezone
    # use enum type for states
    #state = Column(String(64), default='start|-1', nullable=False)

    student = relationship('Student', use_list=False, back_populates='user')

    def __repr__(self):
        return f'<User[{self.user_id}] {self.username}>'


class Student(Base):

    __tablename__ = 'students'

    student_id = Column(Integer, primary_key=True)
    user_id = Column(foreign_key=('users.user_id'))
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    avg_grade = Column(Float(32), nullable=True)

    user = relationship('User', back_populates='student')

    submissions = relationship('Submission', back_populates='student',
                               cascade='all, delete, delete-orphan')

    def __repr__(self):
        return f'<Student[{self.student_id}] {self.first_name} ' \
                '{self.last_name}>'


class Submission(Base):

    __tablename__ = 'submissions'
    __table_args__ = (UniqueConstraint('hw_id', 'student_id',
                                       'submission_id'),)

    submission_id = Column(Integer, primary_key=True)
    # Each submission is a tuple (student_id, hw_id, submission_id) to identify
    # student submitted a work, homework's serial number, submission number
    # (e.g. Bershatsky submitted his 3rd attempt at solution to hw #3.
    student_id = Column(foreign_key=('students.student_id'))
    hw_id = Column(Integer, nullable=False) # HW number
    ordinal = Column(Integer, nullable=False) # Submission number
    submitted_at = Column(DateTime, default=datetime.now(), nullable=False,
                             server_default=text('NOW()'))
    grade = Column(Float(32), nullable=True) # Grade

    user = relationship('Student', back_populates='submissions')

    def __repr__(self):
        return f'<Submission[id={self.submission_id}] student' \
                'name={self.student_id} HW #{self.hw_id} ' \
                'attempt #{self.ordinal}>'
