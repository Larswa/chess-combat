# CRUD operations for DB access
from .models import Player, Game, Move
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chess:chess@localhost:5432/chess")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_player(db, name):
    # Check if player already exists
    existing_player = db.query(Player).filter(Player.name == name).first()
    if existing_player:
        return existing_player
    
    player = Player(name=name)
    db.add(player)
    db.commit()
    db.refresh(player)
    return player

def create_game(db, white_id, black_id):
    game = Game(white_id=white_id, black_id=black_id)
    db.add(game)
    db.commit()
    db.refresh(game)
    return game

def add_move(db, game_id, move):
    move_obj = Move(game_id=game_id, move=move)
    db.add(move_obj)
    db.commit()
    db.refresh(move_obj)
    return move_obj

def get_game(db, game_id):
    return db.query(Game).filter(Game.id == game_id).first()
