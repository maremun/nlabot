#   encoding: utf-8
#   models.py

from datetime import datetime
from sqlalchemy import ARRAY, Boolean, Column, DateTime, Float, ForeignKey, \
    Integer, String, UniqueConstraint, create_engine
from sqlalchemy.ext.declarative import as_declarative
from sqlalchemy.dialects.postgresql import ENUM
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


StateType = ENUM('registered', 'unregistered', name='state_type')


class User(Base):

    __tablename__ = 'users'

    user_id = Column(Integer, primary_key=True)
    student_id = Column(ForeignKey('students.student_id'), unique=True)
    username = Column(String(64), nullable=True)
    first_name = Column(String(64), nullable=True)
    last_name = Column(String(64), nullable=True)
    last_seen_at = Column(DateTime, default=datetime.now, nullable=False)
    # TODO add server_default with timezone
    state = Column(StateType, server_default='unregistered', nullable=False)

    student = relationship('Student', back_populates='users')

    def __repr__(self):
        return f'<User[{self.user_id}] {self.username}>'


class Student(Base):

    __tablename__ = 'students'

    student_id = Column(Integer, primary_key=True)
    first_name = Column(String(64), nullable=False)
    last_name = Column(String(64), nullable=False)
    # the account to identify a student
    account = Column(String(128), nullable=False)
    grades = Column(ARRAY(Float(32)), default=[0, 0, 0], nullable=False)

    users = relationship('User', back_populates='student',
                         cascade='all, delete, delete-orphan')
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
    file_id = Column(String(128), unique=True)
    path = Column(String(256))
    # Each submission is a tuple (student_id, hw_id, submission_id) to identify
    # student submitted a work, homework's serial number, submission number
    # (e.g. Student1 submitted his 3rd attempt at solution to hw #3.
    student_id = Column(ForeignKey('students.student_id'))
    hw_id = Column(ForeignKey('homeworks.hw_id'))
    ordinal = Column(Integer, nullable=False)  # Submission number
    submitted_at = Column(DateTime, default=datetime.now(), nullable=False,
                          server_default=text('NOW()'))
    grade = Column(Float(32), nullable=True)  # Grade
    grades = Column(ARRAY(Float(32)), nullable=True)  # Grades
    expired = Column(Boolean, nullable=False)

    student = relationship('Student', back_populates='submissions')
    homework = relationship('Homework', back_populates='submissions')

    def __repr__(self):
        return f'<Submission[id={self.submission_id}] student' \
                'name={self.student_id} HW #{self.hw_id} ' \
                'attempt #{self.ordinal}>'


class Homework(Base):

    __tablename__ = 'homeworks'

    hw_id = Column(Integer, primary_key=True)
    pts_per_func = Column(ARRAY(Integer), nullable=False)
    deadline = Column(DateTime, nullable=False)

    submissions = relationship('Submission', back_populates='homework',
                               cascade='all, delete, delete-orphan')

    def __repr__(self):
        return f'<Homework[{self.hw_id}] {self.total_pts} ' \
                '{self.n_func} {self.pts_per_func}>'
