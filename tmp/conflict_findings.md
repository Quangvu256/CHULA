# Finding: two inter-standard normative conflicts, with proposed reconciliations

RESEARCH FRAMING. The knowledge graph made two contradictions between ISO
19650-5 and ISO 19650-6 machine-detectable (query: `MATCH (a)-[r]->(b) WHERE
r.note STARTS WITH 'CONFLICT' RETURN a,r,b`) - obligations that are each
normative ('shall') in their own document and mutually incompatible in
implementation. Reading the parts separately, the collision is easy to miss;
in the merged graph it is one query. This is a direct argument for
graph-based extraction over per-document, per-sentence pipelines.

For a deployed system these would be governance decisions; for this research
they are FINDINGS, and the options analysis below is the PROPOSED
RECONCILIATION - a contribution in its own right. No sign-off applies.

## Decision 1 - append-only history vs information purging

**The conflict.** ISO 19650-6 (Tables 1-4, History field): "Entries shall not be
deleted" - risk/incident records are append-only. ISO 19650-5 (B.4.2): the
information lifecycle includes purging, and secure disposal/destruction is part
of information security policy (B.4.1 b). One rule forbids deletion, the other
requires it.

**Options.**
- (a) Purge payload, keep the audit entry: personal/sensitive content is removed
  at end-of-life, but an anonymized append-only stub (id, timestamps, category,
  hash of removed content) stays forever.
- (b) Scope the rules by copy: the register of record is append-only (P6 rule);
  every derived copy - exports, caches, training snapshots - is purgeable
  (P5 rule).
- (c) Time-boxed register: append-only within a retention window, purged after.

**Proposed reconciliation: (a) + (b) combined.** The register keeps an append-only spine
of stubs (satisfying P6's audit intent and PdM's need for an immutable training
timeline), personal/protected payloads are purgeable within the stubs
(satisfying P5 and privacy law), and all derived copies are plainly purgeable.
Rationale: this is the only option where BOTH standards' intents survive intact;
(c) breaks the PdM training timeline at the window boundary.

**Consequence for a PdM implementation:** the timeseries store keeps raw telemetry
under (b) rules; the H&S register keeps stubs forever; model-training snapshots
are versioned, purgeable artifacts.


## Decision 2 - share-all vs assess-before-share

**The conflict.** ISO 19650-6 (4.5.2): parties "shall share all generated health
and safety information with all parties". ISO 19650-5 (7.2): an assessment is
required before sharing/publishing information to third parties. 19650-6 (4.5.5)
acknowledges the tension ("whilst remaining security-minded") but sets no
precedence.

**Options.**
- (a) Share-first: 4.5.2 wins; assessment only for external/third parties.
- (b) Assess-first: every share passes the P5 assessment; 4.5.2 satisfied with
  whatever survives it.
- (c) Two-tier: within the appointed project/asset team, share-all applies
  immediately (these parties are already inside the security perimeter of the
  appointment); to anyone OUTSIDE the appointment chain, the P5 third-party
  provision assessment runs first and generalized information (19650-6, 3.3)
  is the sharing currency.

**Proposed reconciliation: (c).** It matches the letter of both texts: 4.5.2's "all
parties" reads naturally as the parties of the appointment, and P5's 7.2 is
explicitly about provision to third parties. On a sensitive built asset
(security triage outcome ST1/ST2) the assessment additionally gates internal
sharing - that stricter posture comes from the triage outcome, not from a
blanket rule.

**Consequence for a PdM implementation:** dashboards and alerts flow freely inside the
project/asset team; any external export (vendor benchmarking, research datasets,
regulator submissions) passes the assessment and carries generalized records
(role-based identification per ISO 19650-6, Table A.1 footnote b).

