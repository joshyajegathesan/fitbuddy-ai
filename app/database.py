from sqlalchemy import create_engine, Column, Integer, String, Text, Float
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings


Base = declarative_base()


# Database connection
connect_args = {}

if settings.database_url.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.database_url,
    connect_args=connect_args
)

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), unique=True, index=True)
    username = Column(String(100), nullable=False)
    age = Column(Integer, nullable=False)
    weight = Column(Float, nullable=False)
    goal = Column(String(100), nullable=False)
    intensity = Column(String(100), nullable=False)


class Plan(Base):
    __tablename__ = "plans"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(String(100), index=True)
    workout_plan = Column(Text, nullable=False)
    nutrition_tip = Column(Text, nullable=True)
    feedback = Column(Text, nullable=True)


def init_db():
    Base.metadata.create_all(bind=engine)


def save_user(user_data):
    db = SessionLocal()

    try:
        user = User(**user_data)
        db.add(user)
        db.commit()
        db.refresh(user)
        return user
    finally:
        db.close()


def save_plan(plan_data):
    db = SessionLocal()

    try:
        plan = Plan(**plan_data)
        db.add(plan)
        db.commit()
        db.refresh(plan)
        return plan
    finally:
        db.close()


def get_user(user_id):
    db = SessionLocal()

    try:
        return (
            db.query(User)
            .filter(User.user_id == user_id)
            .first()
        )
    finally:
        db.close()


def get_plan(user_id):
    db = SessionLocal()

    try:
        return (
            db.query(Plan)
            .filter(Plan.user_id == user_id)
            .order_by(Plan.id.desc())
            .first()
        )
    finally:
        db.close()


def update_plan(plan_id, workout_plan, feedback=None):
    db = SessionLocal()

    try:
        plan = (
            db.query(Plan)
            .filter(Plan.id == plan_id)
            .first()
        )

        if plan:
            plan.workout_plan = workout_plan

            if feedback is not None:
                plan.feedback = feedback

            db.commit()
            db.refresh(plan)

        return plan

    finally:
        db.close()


def get_all_users():
    db = SessionLocal()

    try:
        return (
            db.query(User)
            .order_by(User.id.desc())
            .all()
        )
    finally:
        db.close()