# Codex working instructions

Read README.md and docs/01-PRODUCT-SCOPE.md through docs/06-CODEX-HANDOFF.md before implementing.

## Non-negotiable project scope

We are building World Classification Atlas, not Demand Atlas. Catalogues first; real-world instances/providers later and **out of scope now**. No fixed human-needs ontology. The 15 domains are discovery/navigation groupings, not authoritative ontological categories.

## Preferred work style

Keep an explicit final-state vision while implementing in dependency order. Avoid repeatedly inventing “MVP/v1/v2” product goals. Prioritize actual abilities over elaborate scaffolding or defensive ceremony.

Treat source metadata as candidates until verified. Preserve official structure, version, IDs and definitions, and separate raw snapshots, parsed source schemes, and Atlas-created schemes. Never invent official code counts or machine-generated source definitions. Check redistribution rights before adding raw standards to the public repo.

Every completed task should report source links, reproducible commands, coverage and counts obtained from actual files, failures, caveats, and git commit. Prefer small real samples to prove parsers/mappings, then scale without changing the goal.

Start with classification discovery/registry and source metadata, then authenticated/downloadable local assets, then per-domain normalization and fusion, then atlas browsing. Do not implement entity-instance relationships.
