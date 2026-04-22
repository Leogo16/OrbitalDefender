from settings import HIGHSCORE_FILE

def load_highscore() -> int:
    try:
        with open(HIGHSCORE_FILE, "r") as f:
            return int(f.read().strip())
    except (FileNotFoundError, ValueError):
        return 0


def save_highscore(score: int) -> bool:
    current = load_highscore()
    if score > current:
        with open(HIGHSCORE_FILE, "w") as f:
            f.write(str(score))
        return True
    return False
