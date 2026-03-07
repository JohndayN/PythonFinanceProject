from .core import fetch_board
from .__init__ import get_market_data, list_boards

if __name__ == "__main__":
    print("Available boards:")
    for board_id, board_name in list_boards().items():
        print(f"{board_id}: {board_name}")

    try:
        board_name = input("Enter board name to fetch data: ")
        df = get_market_data(board_name)
        print(df.head())
    except ValueError as ve:
        print(str(ve))