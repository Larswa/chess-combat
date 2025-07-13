# CRUD operations for DB access
from .models import Player, Game, Move
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://chess:chess@localhost:5432/chess")
logger.info(f"Connecting to database: {DATABASE_URL.split('@')[1] if '@' in DATABASE_URL else DATABASE_URL}")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_player(db, name):
    logger.debug(f"Creating player in database: {name}")
    player = Player(name=name)
    db.add(player)
    db.commit()
    db.refresh(player)
    logger.debug(f"Player created with ID: {player.id}")
    return player

def create_game(db, white_id, black_id):
    logger.debug(f"Creating game in database: white_id={white_id}, black_id={black_id}")
    game = Game(white_id=white_id, black_id=black_id)
    db.add(game)
    db.commit()
    db.refresh(game)
    logger.debug(f"Game created with ID: {game.id}")
    return game

def add_move(db, game_id, move):
    logger.debug(f"Adding move to database: game_id={game_id}, move={move}")
    move_obj = Move(game_id=game_id, move=move)
    db.add(move_obj)
    db.commit()
    db.refresh(move_obj)
    logger.debug(f"Move added with ID: {move_obj.id}")
    return move_obj

def get_game(db, game_id):
    logger.debug(f"Fetching game from database: {game_id}")
    game = db.query(Game).filter(Game.id == game_id).first()
    if game:
        logger.debug(f"Game found: {game_id}")
    else:
        logger.debug(f"Game not found: {game_id}")
    return game
