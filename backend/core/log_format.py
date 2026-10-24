# backend\core\log_format.py

import re
from typing import NamedTuple


_LOG_LINE_RE = re.compile(
    r"^\[(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}"
    r"(?:\.\d{3}\s+[+-]\d{2}:\d{2})?)\]\s+"
    r"\[(?P<level>[A-Za-z0-9_]+)\]\s+(?P<msg>.*)$",
    re.DOTALL,
)

LEVEL_ALIASES: dict[str, tuple[str, ...]] = {
    "INF": ("INFO", "INF"),
    "DBG": ("DEBUG", "DBG"),
    "WRN": ("WARNING", "WRN"),
    "ERR": ("ERROR", "ERR"),
    "CRI": ("CRITICAL", "CRI"),
}


class ParsedLogLine(NamedTuple):
    time: str
    level: str
    message: str


def parse_log_line(line: str) -> ParsedLogLine | None:
    match = _LOG_LINE_RE.match(line)
    if match is None:
        return None
    return ParsedLogLine(
        time=match.group("time"),
        level=match.group("level"),
        message=match.group("msg"),
    )


def log_level_matches(level: str, filter_level: str, all_label: str) -> bool:
    if filter_level == all_label:
        return True
    level_upper = level.upper()
    filter_upper = filter_level.upper()
    return level_upper == filter_upper or level_upper in LEVEL_ALIASES.get(
        filter_upper, (filter_upper,)
    )
