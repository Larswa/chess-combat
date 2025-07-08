import openai
import os

def get_openai_chess_move(board_fen, move_history):
    client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    prompt = f"You are a chess engine. Given the current board in FEN: {board_fen} and move history: {move_history}, return the best next move in UCI format (e.g., e2e4). Only return the move."
    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        # model="gpt-4o",
        messages=[
            {"role": "system", "content": "You are a chess engine."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=10,
        temperature=0.2
    )
    move = response.choices[0].message.content.strip()
    return move