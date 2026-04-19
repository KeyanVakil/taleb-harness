#!/usr/bin/env python3
"""No ghosts: reject writes that ADD TODO/FIXME/XXX/HACK markers.
Pre-existing markers are tolerated."""
import re
from _lib import before_after, fail, read_payload

PATTERN = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")


def main() -> None:
    ba = before_after(read_payload())
    if ba is None:
        return
    before, after, _ = ba
    added = len(PATTERN.findall(after)) - len(PATTERN.findall(before))
    if added > 0:
        fail(
            f"No ghosts: this change adds {added} new "
            f"TODO/FIXME/XXX/HACK marker(s). Do the thing now or delete "
            f"the concern from the code."
        )


if __name__ == "__main__":
    main()
