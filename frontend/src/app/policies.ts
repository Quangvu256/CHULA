import { Component } from '@angular/core';

@Component({
  selector: 'policies-tab',
  template: `<div class="pol">
<p class="sub" style="margin-top:4px">What this project does and does not do with data. Research
  software - plain statements, no legalese.</p>

  <h2>Your uploaded IFC models</h2>
  <ul>
   <li><b>Processing is entirely local.</b> An uploaded model is written to a temporary file, audited
     in-process, and the temporary file is <b>deleted immediately</b> after the check - success or
     failure. Nothing is transmitted to any external service.</li>
   <li><b>What is kept:</b> nothing. The report exists only in your browser; download it if you want a
     record. The server prints a single console line (file name, verdict, score) to its own terminal.</li>
   <li><b>No cookies, no analytics, no trackers, no external requests.</b> This page is fully
     self-contained; the only outbound link is the Neo4j Browser link you click yourself.</li>
  </ul>

  <h2>Copyright of the source standards</h2>
  <ul>
   <li>The ISO 19650 series is copyrighted by ISO/BSI. <b>The PDFs are never distributed</b> with this
     repository or Docker image; each team member supplies licensed copies.</li>
   <li>The extraction JSONs and the Cypher export contain limited verbatim definitions with clause-level
     provenance, produced for research purposes, and are <b>excluded from version control</b> - they are
     shared within the project team only.</li>
   <li>The audit report shown to you cites <i>clause numbers</i>, not the standards' text - verify
     wording against your own licensed copy.</li>
  </ul>

  <h2>Personal data inside health-and-safety records</h2>
  <ul>
   <li>The ISO 19650-6 schema fields <i>Affected party / Raised by / Owned by</i> can identify people.
     The standard itself notes "privacy can need protection" and prefers organizational, project or
     role-based identification over personal identification (Table A.1, footnote b). This project adopts
     that as policy for any instance data it ever holds.</li>
   <li>Generalization (ISO 19650-6, 3.3) - removing or replacing personal and protected characteristics -
     is the required step before any wider sharing of learning material.</li>
  </ul>

  <h2>Data governance defaults (proposed)</h2>
  <p class="src">The knowledge graph machine-detected two contradictory obligations between ISO 19650-5
  and ISO 19650-6 (full analysis: <code>tmp/conflict_findings.md</code>). For any deployment, this
  project proposes:</p>
  <ul>
   <li><b>Retention:</b> registers keep an append-only spine of anonymizable stubs forever; sensitive
     payloads within them are purgeable; every derived copy (exports, caches, model-training snapshots)
     is purgeable. Satisfies the ISO 19650-6 no-deletion rule and the ISO 19650-5 purging rule at once.</li>
   <li><b>Sharing:</b> inside the appointed project/asset team, health-and-safety information flows
     freely (ISO 19650-6, 4.5.2); to anyone outside the appointment chain, the ISO 19650-5 third-party
     provision assessment runs first and generalized records are the sharing currency.</li>
  </ul>

  <h2>Security posture of this software</h2>
  <ul>
   <li>The web UI binds to <code>127.0.0.1</code> by default (your machine only); Docker deployments bind
     the container network. There is no authentication layer - do not expose it to untrusted networks.</li>
   <li>Database credentials live in <code>.env</code> (git-ignored), never in code.</li>
   <li>The audit engine parses IFC as plain text with no code execution paths from file content.</li>
  </ul>
  <p class="src">Contact: the project team (Chulalongkorn University research project).</p>
</div>`,
})
export class PoliciesTab {}
