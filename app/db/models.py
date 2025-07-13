# SQLAlchemy models for games, moves, players
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import relationship
import datetime

Base = declarative_base()

class Player(Base):
    __tablename__ = 'players'
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True)
    white_games = relationship('Game', foreign_keys='Game.white_id', back_populates='white')
    black_games = relationship('Game', foreign_keys='Game.black_id', back_populates='black')

class Game(Base):
    __tablename__ = 'games'
    id = Column(Integer, primary_key=True)
    white_id = Column(Integer, ForeignKey('players.id'))
    black_id = Column(Integer, ForeignKey('players.id'))
    created_at = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    moves = relationship('Move', back_populates='game')
    white = relationship('Player', foreign_keys=[white_id], back_populates='white_games')
    black = relationship('Player', foreign_keys=[black_id], back_populates='black_games')

class Move(Base):
    __tablename__ = 'moves'
    id = Column(Integer, primary_key=True)
    game_id = Column(Integer, ForeignKey('games.id'))
    move = Column(String)
    timestamp = Column(DateTime, default=lambda: datetime.datetime.now(datetime.UTC))
    game = relationship('Game', back_populates='moves')
