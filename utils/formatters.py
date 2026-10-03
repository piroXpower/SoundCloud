import math

def format_duration(seconds: int) -> str:
    """Format seconds into HH:MM:SS or MM:SS."""
    if not seconds or seconds <= 0:
        return "Live Stream 🔴"
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"

def get_progress_bar(current_sec: int, total_sec: int, length: int = 12) -> str:
    """Generates an aesthetic Unicode progress bar."""
    if total_sec <= 0:
        return "🔘" + "─" * (length - 1)
    
    percent = min(1.0, max(0.0, current_sec / total_sec))
    filled = math.floor(percent * length)
    empty = length - filled - 1
    
    if empty < 0:
        empty = 0
        filled = length - 1

    bar = "━" * filled + "🔘" + "─" * empty
    return f"`{bar}`"

def clean_html(text: str) -> str:
    """Escapes HTML entities."""
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )

def humanbytes(size: float) -> str:
    """Convert bytes into human readable format."""
    if not size:
        return "0 B"
    power = 2**10
    n = 0
    units = {0: "B", 1: "KB", 2: "MB", 3: "GB", 4: "TB"}
    while size > power:
        size /= power
        n += 1
    return f"{round(size, 2)} {units[n]}"
