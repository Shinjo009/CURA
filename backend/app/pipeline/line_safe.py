"""Keep an answer's line structure when a sentence level check rewrites it.

Some checks split the answer into sentences and join the kept ones with a space. When one
sentence is dropped, that flattens the opener, bullets and headings into a single line.
`per_line` applies such a check to each line on its own, so a drop only removes that line's
sentence and the rest of the layout stays as the model wrote it.
"""

from __future__ import annotations

from functools import wraps


def per_line(check):
    """Wrap check(answer, *args) -> (text, flags) so multi line answers are checked line by line."""

    @wraps(check)
    def wrapper(answer, *args, **kwargs):
        if not answer or "\n" not in answer:
            return check(answer, *args, **kwargs)
        flags: list[str] = []
        lines: list[str] = []
        for line in answer.split("\n"):
            if not line.strip():
                lines.append(line)
                continue
            text, found = check(line, *args, **kwargs)
            flags.extend(found)
            if text.strip():
                lines.append(text)
        if not flags:
            return answer, []
        return "\n".join(lines), flags

    return wrapper
