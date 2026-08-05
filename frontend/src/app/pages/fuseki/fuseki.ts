import { Component, OnInit, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'fuseki-tab',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
  <div class="fuseki-container">
    <!-- Server Status Header -->
    <div class="status-banner" [class.online]="status().online" [class.offline]="!status().online">
      <div class="banner-left">
        <span class="indicator-dot"></span>
        <div>
          <h3>Apache Jena Fuseki SPARQL Monitoring Server</h3>
          <p class="meta">Server: {{status().server}} | Endpoint: {{status().endpoint}} | Dataset: /{{status().dataset}}</p>
        </div>
      </div>
      <div class="banner-right">
        <span class="badge">{{status().online ? 'SERVICE ONLINE' : 'SERVICE OFFLINE'}}</span>
        <button class="b refresh-btn" (click)="loadStatus()">Refresh Monitor</button>
      </div>
    </div>

    <!-- Live Statistics Cards -->
    <div class="stats-row">
      <div class="stat-card">
        <b class="stat-val">{{status().triples | number}}</b>
        <span class="stat-lbl">RDF Triples (ABox + TBox)</span>
      </div>
      <div class="stat-card">
        <b class="stat-val">{{status().nodes | number}}</b>
        <span class="stat-lbl">ISO 19650 Nodes</span>
      </div>
      <div class="stat-card">
        <b class="stat-val">{{status().rels | number}}</b>
        <span class="stat-lbl">Relational Edges</span>
      </div>
      <div class="stat-card">
        <b class="stat-val pass-text">{{status().shacl_gates}}</b>
        <span class="stat-lbl">SHACL Shapes Quality Gates</span>
      </div>
    </div>

    <!-- Interactive SPARQL Console -->
    <div class="sparql-console">
      <div class="console-header">
        <h4>Live W3C SPARQL Console</h4>
        <div class="preset-selector">
          <label>Preset Query:</label>
          <select [(ngModel)]="selectedPreset" (change)="applyPreset()">
            <option value="1">1. Count Nodes by ISO Standard</option>
            <option value="2">2. Top 10 Concepts with Definitions</option>
            <option value="3">3. High-PdM Relevance Nodes</option>
            <option value="4">4. AIM (Asset Information Model) Relationships</option>
          </select>
        </div>
      </div>

      <textarea class="sparql-input" [(ngModel)]="sparqlQuery" rows="7" placeholder="Enter SPARQL query..."></textarea>
      
      <div class="console-actions">
        <button class="b run-btn" (click)="executeSparql()" [disabled]="loading()">
          {{loading() ? 'Executing SPARQL...' : 'Execute SPARQL Query ▶'}}
        </button>
        <span class="exec-time" *ngIf="execTime() !== null">Execution time: {{execTime()}} ms</span>
      </div>

      <!-- Query Results Output -->
      <div class="results-box" *ngIf="resultData()">
        <div class="results-header" *ngIf="!resultData().error">
          <span>Returned {{bindings().length}} rows</span>
        </div>

        <div class="error-msg" *ngIf="resultData().error">
          <b>SPARQL Error:</b> {{resultData().error}}
        </div>

        <div class="scroll-table" *ngIf="headers().length > 0">
          <table class="data-table">
            <thead>
              <tr>
                <th *ngFor="let h of headers()">{{h}}</th>
              </tr>
            </thead>
            <tbody>
              <tr *ngFor="let row of bindings()">
                <td *ngFor="let h of headers()">{{row[h]?.value || ''}}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
  `,
  styles: [`
    .fuseki-container { padding: 10px 0; }
    .status-banner {
      display: flex; justify-content: space-between; align-items: center;
      padding: 16px 20px; border-radius: 8px; background: #1e293b; color: #fff;
      margin-bottom: 20px; border-left: 6px solid #64748b;
    }
    .status-banner.online { border-left-color: #22c55e; }
    .status-banner.offline { border-left-color: #ef4444; }
    .banner-left { display: flex; align-items: center; gap: 14px; }
    .indicator-dot {
      width: 14px; height: 14px; border-radius: 50%; background: #22c55e;
      box-shadow: 0 0 10px #22c55e;
    }
    .status-banner.offline .indicator-dot { background: #ef4444; box-shadow: 0 0 10px #ef4444; }
    .status-banner h3 { margin: 0 0 4px 0; font-size: 18px; font-weight: 600; color: #fff; }
    .status-banner .meta { margin: 0; font-size: 13px; color: #94a3b8; }
    .badge {
      background: #15803d; color: #dcfce7; padding: 4px 10px; border-radius: 20px;
      font-size: 12px; font-weight: 600; margin-right: 12px;
    }
    .refresh-btn { background: #334155; color: #f8fafc; border: 1px solid #475569; padding: 6px 14px; cursor: pointer; border-radius: 4px; }
    .refresh-btn:hover { background: #475569; }

    .stats-row { display: flex; gap: 16px; margin-bottom: 24px; flex-wrap: wrap; }
    .stat-card {
      flex: 1; min-width: 180px; background: #f8fafc; border: 1px solid #e2e8f0;
      padding: 16px; border-radius: 8px; text-align: center;
    }
    .stat-val { display: block; font-size: 24px; font-weight: 700; color: #0f172a; margin-bottom: 4px; }
    .stat-lbl { font-size: 13px; color: #64748b; }
    .pass-text { color: #16a34a; }

    .sparql-console { background: #fff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; }
    .console-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; }
    .console-header h4 { margin: 0; font-size: 16px; color: #0f172a; }
    .preset-selector label { font-size: 13px; color: #475569; margin-right: 8px; }
    .preset-selector select { padding: 6px 12px; border-radius: 4px; border: 1px solid #cbd5e1; font-size: 13px; }

    .sparql-input {
      width: 100%; box-sizing: border-box; font-family: 'Fira Code', 'Courier New', monospace;
      font-size: 13px; padding: 12px; background: #0f172a; color: #38bdf8; border-radius: 6px;
      border: 1px solid #1e293b; line-height: 1.5; margin-bottom: 12px;
    }
    .console-actions { display: flex; align-items: center; gap: 16px; margin-bottom: 16px; }
    .run-btn { background: #2563eb; color: #fff; border: none; padding: 8px 18px; border-radius: 4px; font-weight: 600; cursor: pointer; }
    .run-btn:hover { background: #1d4ed8; }
    .exec-time { font-size: 13px; color: #64748b; }

    .results-box { border-top: 1px solid #e2e8f0; padding-top: 16px; margin-top: 8px; }
    .results-header { font-size: 13px; font-weight: 600; color: #334155; margin-bottom: 8px; }
    .error-msg { background: #fef2f2; border: 1px solid #fecaca; color: #dc2626; padding: 12px; border-radius: 6px; font-size: 13px; }
    .scroll-table { overflow-x: auto; max-height: 400px; }
    .data-table { width: 100%; border-collapse: collapse; font-size: 13px; text-align: left; }
    .data-table th { background: #f1f5f9; padding: 10px 12px; border: 1px solid #cbd5e1; font-weight: 600; color: #334155; }
    .data-table td { padding: 8px 12px; border: 1px solid #e2e8f0; word-break: break-word; }
    .data-table tr:nth-child(even) { background: #f8fafc; }
  `]
})
export class FusekiTab implements OnInit {
  status = signal<any>({
    online: true,
    server: 'http://localhost:3030',
    endpoint: 'http://localhost:3030/iso19650/sparql',
    dataset: 'iso19650',
    triples: 12447,
    nodes: 388,
    shacl_gates: 'PASS (5/5)'
  });

  selectedPreset = '1';
  sparqlQuery = '';
  loading = signal<boolean>(false);
  execTime = signal<number | null>(null);
  resultData = signal<any>(null);

  presets: any = {
    '1': `PREFIX iso: <http://example.org/iso19650#>\n\nSELECT ?Standard (COUNT(?node) AS ?TotalNodes) WHERE {\n  ?node a iso:IsoNode ;\n        iso:part ?Standard .\n}\nGROUP BY ?Standard\nORDER BY ?Standard`,
    '2': `PREFIX iso: <http://example.org/iso19650#>\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n\nSELECT ?TermID ?TermName ?Definition WHERE {\n  ?node a iso:Concept ;\n        iso:nodeId ?TermID ;\n        rdfs:label ?TermName ;\n        iso:definition ?Definition .\n}\nLIMIT 10`,
    '3': `PREFIX iso: <http://example.org/iso19650#>\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n\nSELECT ?NodeID ?Name ?ISO_Part ?Clause WHERE {\n  ?node a iso:IsoNode ;\n        iso:nodeId ?NodeID ;\n        rdfs:label ?Name ;\n        iso:pdmRelevance "high" ;\n        iso:part ?ISO_Part ;\n        iso:provenanceClause ?Clause .\n}`,
    '4': `PREFIX iso: <http://example.org/iso19650#>\nPREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>\n\nSELECT ?RelationshipType ?TargetNodeID ?TargetName WHERE {\n  ?source iso:nodeId "term_aim" ;\n          ?rel ?target .\n  ?target iso:nodeId ?TargetNodeID ;\n          rdfs:label ?TargetName .\n  BIND(STRAFTER(STR(?rel), "#") AS ?RelationshipType)\n}`
  };

  ngOnInit() {
    this.loadStatus();
    this.applyPreset();
  }

  loadStatus() {
    fetch('/api/fuseki/status')
      .then(res => res.json())
      .then(data => this.status.set(data))
      .catch(() => this.status.update(s => ({ ...s, online: false })));
  }

  applyPreset() {
    this.sparqlQuery = this.presets[this.selectedPreset] || '';
  }

  executeSparql() {
    if (!this.sparqlQuery.trim()) return;
    this.loading.set(true);
    this.resultData.set(null);
    const start = performance.now();

    fetch('/api/fuseki/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query: this.sparqlQuery })
    })
      .then(res => res.json())
      .then(data => {
        this.execTime.set(Math.round(performance.now() - start));
        this.resultData.set(data);
        this.loading.set(false);
      })
      .catch(err => {
        this.execTime.set(Math.round(performance.now() - start));
        this.resultData.set({ error: err.message });
        this.loading.set(false);
      });
  }

  headers(): string[] {
    const r = this.resultData();
    return r?.head?.vars || [];
  }

  bindings(): any[] {
    const r = this.resultData();
    return r?.results?.bindings || [];
  }
}
