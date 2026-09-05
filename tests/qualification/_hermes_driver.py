"""Dispatch plugin tools through the real Hermes runtime, deterministically.

Runs under the Hermes v0.20.5 venv interpreter with ``HERMES_HOME`` pointed
at a disposable profile: importing :mod:`model_tools` performs the real
built-in tool discovery and the real plugin discovery over the enabled
plugin, and every case is dispatched through
``model_tools.handle_function_call`` — the same dispatcher the agent loop
and the Hermes tools MCP server use for every tool call. No model, no
network, no agent session: the dispatch path is deterministic.

Usage: ``python _hermes_driver.py <manifest.json>`` where the manifest is a
list of ``{"tool": ..., "args": {...}}`` cases. The single-line stdout
result is ``{"results": [{"tool", "args", "raw"}, ...]}`` with ``raw``
carrying the dispatcher's JSON reply verbatim.
"""

from __future__ import annotations

import json
import os
import sys


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: _hermes_driver.py <manifest.json>", file=sys.stderr)
        return 2
    with open(sys.argv[1], encoding="utf-8") as handle:
        cases = json.load(handle)
    os.environ.setdefault("HERMES_QUIET", "1")

    # The import is the runtime bootstrap: it discovers built-in tools and
    # loads the enabled plugins from HERMES_HOME before anything is called.
    import model_tools

    results = []
    for case in cases:
        raw = model_tools.handle_function_call(case["tool"], case["args"])
        results.append({"tool": case["tool"], "args": case["args"], "raw": raw})
    print(json.dumps({"results": results}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
