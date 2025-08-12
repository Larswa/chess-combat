"""
AI Session Manager for maintaining chess game context and strategic continuity
"""
import logging
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
import threading

logger = logging.getLogger(__name__)

@dataclass
class ChessSession:
    """Represents a persistent chess AI session with memory and strategy"""
    session_id: str
    created_at: float = field(default_factory=time.time)
    last_access: float = field(default_factory=time.time)
    move_history: List[str] = field(default_factory=list)
    strategic_memory: Dict[str, Any] = field(default_factory=dict)
    ai_provider: str = "openai"  # "openai" or "gemini"
    conversation_context: List[Dict[str, str]] = field(default_factory=list)
    game_analysis: Dict[str, Any] = field(default_factory=dict)

    def update_access_time(self):
        """Update the last access time"""
        self.last_access = time.time()

    def add_move(self, move: str):
        """Add a move to the session history"""
        self.move_history.append(move)
        self.update_access_time()

    def get_game_phase(self) -> str:
        """Determine current game phase based on move count"""
        move_count = len(self.move_history)
        if move_count < 20:
            return "opening"
        elif move_count < 40:
            return "middlegame"
        else:
            return "endgame"

    def add_strategic_insight(self, key: str, value: Any):
        """Add strategic insight to session memory"""
        self.strategic_memory[key] = value
        self.update_access_time()

    def get_strategic_insight(self, key: str, default=None):
        """Get strategic insight from session memory"""
        return self.strategic_memory.get(key, default)

class AISessionManager:
    """Manages persistent AI sessions for strategic chess gameplay"""

    def __init__(self, session_timeout: int = 3600):  # 1 hour default timeout
        self.sessions: Dict[str, ChessSession] = {}
        self.session_timeout = session_timeout
        self._lock = threading.Lock()
        logger.info("AI Session Manager initialized")

    def create_session(self, session_id: str, ai_provider: str = "openai") -> ChessSession:
        """Create a new AI session"""
        with self._lock:
            if session_id in self.sessions:
                logger.info(f"Session {session_id} already exists, returning existing session")
                return self.sessions[session_id]

            session = ChessSession(
                session_id=session_id,
                ai_provider=ai_provider
            )
            self.sessions[session_id] = session
            logger.info(f"Created new AI session: {session_id} with provider: {ai_provider}")
            return session

    def get_session(self, session_id: str) -> Optional[ChessSession]:
        """Get an existing session"""
        with self._lock:
            session = self.sessions.get(session_id)
            if session:
                session.update_access_time()
                return session
            return None

    def cleanup_expired_sessions(self):
        """Remove expired sessions"""
        current_time = time.time()
        expired_sessions = []

        with self._lock:
            for session_id, session in self.sessions.items():
                if current_time - session.last_access > self.session_timeout:
                    expired_sessions.append(session_id)

            for session_id in expired_sessions:
                del self.sessions[session_id]
                logger.info(f"Cleaned up expired session: {session_id}")

        return len(expired_sessions)

    def get_strategic_move(self, session_id: str, board_fen: str, move_history: List[str],
                          invalid_moves: List[str] = None) -> Optional[str]:
        """Get a strategic move using session context and avoiding invalid moves"""
        session = self.get_session(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found for strategic move")
            return None

        try:
            # Update session with current state
            session.move_history = move_history.copy()
            session.update_access_time()

            # Store invalid moves in session memory to avoid repetition
            if invalid_moves:
                session.add_strategic_insight("invalid_moves_current_position", invalid_moves)
                logger.debug(f"Session {session_id}: tracking {len(invalid_moves)} invalid moves")

            # Build conversation context for strategic thinking
            game_phase = session.get_game_phase()

            # Create strategic context based on game phase and history
            strategic_context = self._build_strategic_context(session, board_fen)
            strategic_context["invalid_moves"] = invalid_moves or []

            # Call the appropriate AI provider with enhanced context
            if session.ai_provider == "openai":
                return self._get_openai_strategic_move(session, strategic_context)
            elif session.ai_provider == "gemini":
                return self._get_gemini_strategic_move(session, strategic_context)
            else:
                logger.error(f"Unknown AI provider: {session.ai_provider}")
                return None

        except Exception as e:
            logger.error(f"Error getting strategic move for session {session_id}: {e}")
            return None

    def _build_strategic_context(self, session: ChessSession, board_fen: str) -> Dict[str, Any]:
        """Build strategic context for AI decision making"""
        from .chess_helper import get_position_description

        context = {
            "board_fen": board_fen,
            "game_phase": session.get_game_phase(),
            "move_count": len(session.move_history),
            "position_description": get_position_description(board_fen),
            "strategic_memory": session.strategic_memory.copy(),
            "recent_moves": session.move_history[-10:] if session.move_history else []
        }

        # Add game phase specific strategic considerations
        if context["game_phase"] == "opening":
            context["strategic_focus"] = "development, center control, king safety"
        elif context["game_phase"] == "middlegame":
            context["strategic_focus"] = "tactics, positional play, piece coordination"
        else:  # endgame
            context["strategic_focus"] = "king activity, pawn promotion, precise calculation"

        return context

    def _get_openai_strategic_move(self, session: ChessSession, context: Dict[str, Any]) -> Optional[str]:
        """Get strategic move from OpenAI with session context"""
        import openai
        import os
        import chess

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            logger.error("OPENAI_API_KEY not set for strategic move")
            return None

        client = openai.OpenAI(api_key=api_key)

        # Get all legal moves
        board = chess.Board(context['board_fen'])
        all_legal_moves = [move.uci() for move in board.legal_moves]

        # Build enhanced prompt with session memory
        system_prompt = f"""You are a chess grandmaster with perfect memory of this game session.

SESSION CONTEXT:
- Game Phase: {context['game_phase']}
- Strategic Focus: {context['strategic_focus']}
- Move Count: {context['move_count']}
- Session Memory: {context['strategic_memory']}

IMPORTANT: Maintain strategic continuity from previous moves in this session.
Consider long-term positional goals and tactical themes that have emerged.

You must respond in this EXACT format:
MOVE: [uci_move]
REASON: [strategic_explanation]
STRATEGY: [long_term_plan]"""

        recent_moves_text = " ".join(context['recent_moves'][-6:]) if context['recent_moves'] else "Game start"

        user_prompt = f"""POSITION (FEN): {context['board_fen']}

ALL LEGAL MOVES: {', '.join(all_legal_moves[:30])}{'...' if len(all_legal_moves) > 30 else ''}

RECENT MOVES: {recent_moves_text}

Based on our session history and strategic memory, choose the best move that maintains our long-term strategy while addressing immediate tactical needs."""

        try:
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=150,
                temperature=0.2
            )

            ai_response = response.choices[0].message.content.strip()
            logger.debug(f"OpenAI strategic response: {ai_response}")

            # Parse the structured response
            from .openai_ai import parse_structured_move_response
            move = parse_structured_move_response(ai_response, all_legal_moves)

            if move:
                # Extract and store strategic insights
                self._extract_strategic_insights(session, ai_response)
                return move

        except Exception as e:
            logger.error(f"OpenAI strategic move error: {e}")

        return None

    def _get_gemini_strategic_move(self, session: ChessSession, context: Dict[str, Any]) -> Optional[str]:
        """Get strategic move from Gemini with session context"""
        # Similar implementation for Gemini
        logger.info("Gemini strategic moves not yet implemented, falling back to standard")
        return None

    def _extract_strategic_insights(self, session: ChessSession, ai_response: str):
        """Extract and store strategic insights from AI response"""
        try:
            # Look for STRATEGY: line in response
            if "STRATEGY:" in ai_response:
                strategy_line = ai_response.split("STRATEGY:")[1].strip()
                session.add_strategic_insight("latest_strategy", strategy_line)

            # Store response for conversation continuity
            session.conversation_context.append({
                "timestamp": str(time.time()),
                "response": ai_response,
                "game_phase": session.get_game_phase()
            })

            # Keep only recent conversation context (last 5 exchanges)
            if len(session.conversation_context) > 5:
                session.conversation_context = session.conversation_context[-5:]

        except Exception as e:
            logger.warning(f"Error extracting strategic insights: {e}")

    def get_session_stats(self) -> Dict[str, Any]:
        """Get statistics about active sessions"""
        with self._lock:
            stats = {
                "active_sessions": len(self.sessions),
                "sessions_by_provider": {},
                "average_moves_per_session": 0,
                "total_moves": 0
            }

            if not self.sessions:
                return stats

            # Calculate provider distribution
            for session in self.sessions.values():
                provider = session.ai_provider
                stats["sessions_by_provider"][provider] = stats["sessions_by_provider"].get(provider, 0) + 1
                stats["total_moves"] += len(session.move_history)

            stats["average_moves_per_session"] = stats["total_moves"] / len(self.sessions)

            return stats

# Global session manager instance
session_manager = AISessionManager(session_timeout=3600)  # 1 hour timeout
session_manager = AISessionManager()

def get_session_manager() -> AISessionManager:
    """Get the global session manager instance"""
    return session_manager
