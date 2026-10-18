def initial_cursor(total_rows: int, warmup_steps: int = 12) -> int:
    if total_rows <= 0:
        raise ValueError("simulation requires observations")
    return min(max(0, warmup_steps), total_rows - 1)

def advance_cursor(current: int, total_rows: int, steps: int = 1) -> int:
    if total_rows <= 0:
        raise ValueError("simulation requires observations")
    if steps < 1:
        raise ValueError("steps must be positive")
    return min(current + steps, total_rows - 1)
