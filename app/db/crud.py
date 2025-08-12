# CRUD operations for DB access
from .models import Player, Game, Move
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import logging
import datetime

logger = logging.getLogger(__name__)

# Global variables for dependency injection
_engine = None
_session_local = None

def set_database_engine(engine):
    """Set the database engine for dependency injection (mainly for testing)"""
    global _engine, _session_local
    _engine = engine
    _session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info(f"Database engine set for injection: {engine}")

def get_engine():
    """Get the database engine, creating it if necessary"""
    global _engine
    if _engine is None:
        database_url = os.getenv("DATABASE_URL", "postgresql://chess:chess@localhost:5432/chess")
        logger.info(f"Creating database engine for: {database_url.split('@')[0] if '@' in database_url else database_url}")
        _engine = create_engine(database_url)
    logger.info(f"Returning database engine: {_engine}")
    return _engine

def get_session_local():
    """Get the session factory, creating it if necessary"""
    global _session_local
    if _session_local is None:
        # Make sure we use the same engine instance
        engine = get_engine()
        _session_local = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info(f"Created session factory with engine: {engine}")
    return _session_local

def create_player(db, name):
    logger.debug(f"Creating or finding player: {name}")
    # Check if player already exists
    existing_player = db.query(Player).filter(Player.name == name).first()
    if existing_player:
        logger.debug(f"Player {name} already exists with ID: {existing_player.id}")
        return existing_player

    logger.info(f"Creating new player: {name}")
    player = Player(name=name)
    db.add(player)
    db.commit()
    db.refresh(player)
    logger.info(f"Successfully created player {name} with ID: {player.id}")
    return player

def create_player_strict(db, name):
    """Create a player, raising IntegrityError if name already exists"""
    logger.debug(f"Creating player (strict mode): {name}")
    # Check if player already exists
    existing_player = db.query(Player).filter(Player.name == name).first()
    if existing_player:
        logger.warning(f"Player {name} already exists (strict mode)")
        from sqlalchemy.exc import IntegrityError
        raise IntegrityError("Player name already exists", None, None)

    logger.info(f"Creating new player (strict): {name}")
    player = Player(name=name)
    db.add(player)
    db.commit()
    db.refresh(player)
    logger.info(f"Successfully created player {name} with ID: {player.id}")
    return player

def create_game(db, white_id, black_id):
    logger.info(f"Creating game: white_id={white_id}, black_id={black_id}")
    game = Game(white_id=white_id, black_id=black_id)
    db.add(game)
    db.commit()
    db.refresh(game)
    logger.info(f"Successfully created game with ID: {game.id}")
    return game

def add_move(db, game_id, move):
    logger.debug(f"Adding move '{move}' to game {game_id}")
    move_obj = Move(game_id=game_id, move=move)
    db.add(move_obj)
    db.commit()
    db.refresh(move_obj)
    logger.debug(f"Successfully added move with ID: {move_obj.id}")
    return move_obj

def get_game(db, game_id):
    logger.debug(f"Fetching game with ID: {game_id}")
    game = db.query(Game).filter(Game.id == game_id).first()
    if game:
        logger.debug(f"Found game {game_id}")
    else:
        logger.debug(f"Game {game_id} not found")
    return game

def update_game_result(db, game_id, result, termination):
    """Update game with final result when it ends"""
    logger.info(f"Updating game {game_id} with result: {result}, termination: {termination}")
    game = db.query(Game).filter(Game.id == game_id).first()
    if game:
        game.is_finished = "true"
        game.result = result
        game.termination = termination
        game.finished_at = datetime.datetime.now(datetime.UTC)
        db.commit()
        db.refresh(game)
        logger.info(f"Successfully updated game {game_id} with final result")
        return game
    else:
        logger.error(f"Game {game_id} not found for result update")
        return None
