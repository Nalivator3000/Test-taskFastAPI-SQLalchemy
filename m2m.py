from sqlalchemy import create_engine, Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import declarative_base, relationship, joinedload, sessionmaker, Session
from typing import List
from pydantic import BaseModel
from fastapi import FastAPI, Query, Depends


# Make the engine
engine = create_engine('postgresql+psycopg2://postgres:03061994@localhost/test_task_db', echo=True)

# Make the DeclarativeMeta
Base = declarative_base()

app = FastAPI()


# Declare Classes / Tables
game_users = Table('game_users', Base.metadata,
                     Column('game_id', ForeignKey('games.id'), primary_key=True),
                     Column('user_id', ForeignKey('users.id'), primary_key=True)
                     )


class Game(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    users = relationship("User", secondary="game_users", back_populates='games')


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    email = Column(String, nullable=False, unique=True)
    games = relationship("Game", secondary="game_users", back_populates='users')


class UserBase(BaseModel):
    id: int
    name: str
    age: int = Query(ge=0, le=100)
    email: str

    class Config:
        orm_mode = True


class GameBase(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True


class UsersOut(UserBase):
    games: List[GameBase]


class GamesOut(GameBase):
    users: List[UserBase]


# Create the tables in the database
Base.metadata.create_all(engine)


def get_db():
    db_start = Session(bind=engine)
    try:
        yield db_start
    finally:
        db_start.close()


db: Session = Depends(get_db)


# with Session(bind=engine) as session:
#     game1 = Game(name="Game1")
#     game2 = Game(name="Game2")
#
#     user1 = User(name="User1", age=11, email='1@mail.com')
#     user2 = User(name="User3", age=33, email='3@mail.com')
#     user3 = User(name="User2", age=22, email='2@mail.com')
#
#     session.add_all([game1, game2, user1, user2, user3])
#     session.commit()


@app.get("/games/{id}", response_model=GamesOut)
def get_game(id: int, db: Session = Depends(get_db)):
    db_game = db.query(Game).options(joinedload(Game.users)). \
        where(Game.id == id).one()
    return db_game


@app.get("/games", response_model=List[GamesOut])
def get_games(db: Session = Depends(get_db)):
    db_games = db.query(Game).options(joinedload(Game.users)).all()
    return db_games


@app.get("/users/{id}", response_model=UsersOut)
def get_user(id: int, db: Session = Depends(get_db)):
    db_user = db.query(User).options(joinedload(User.games)). \
        where(User.id == id).one()
    return db_user


@app.get("/users", response_model=List[UsersOut])
def get_users(db: Session = Depends(get_db)):
    db_users = db.query(User).options(joinedload(User.games)).all()
    return db_users


@app.post('/connect/{uid}/{gid}')
def connect_to_game(uid: int, gid: int, db: Session = Depends(get_db)):
    game = db.query(Game).filter(Game.id == gid).first()
    user = db.query(User).filter(User.id == uid).first()

    user.games.append(game)
    game.users.append(user)

    db.commit()

    return f'{game.name} successfully connected to {user.name}'


def 
