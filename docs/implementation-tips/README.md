# Implementation Tips

This role contains non-normative guidance discovered during delivery. Tips may
explain local commands, debugging techniques, and known traps, but they cannot
change the PRD, an accepted ADR, or roadmap lifecycle.

Initial cautions:

- derive manifest, registry parity, schema inventory, and command descriptors
  from one declarative source;
- keep all process creation in runner.py;
- test argv as arrays and never build shell command strings;
- use concurrent bounded stream draining to avoid deadlocks;
- keep qualification profiles disposable and isolated.
