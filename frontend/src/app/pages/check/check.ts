import { Component, inject, signal } from '@angular/core';
import { Api } from '../../core/api';
import { AppState } from '../../core/state';

@Component({
  selector: 'check-tab',
  template: `
  <div class="stats">
    @if (kg(); as k) {
      <div class="stat"><b>{{k.nodes}}</b><span>KG nodes</span></div>
      <div class="stat"><b>{{k.rels}}</b><span>relationships</span></div>
      <div class="stat"><b>{{k.high}}</b><span>high&#8209;PdM</span></div>
      <div class="stat"><b>{{k.parts.length}}</b><span>standards</span></div>
      <div class="stat" style="min-width:auto">
        <b style="font-size:14px;padding-top:3px"><a [href]="k.browser" target="_blank" rel="noopener">Apache Jena Fuseki &#8599;</a></b>
        <span>SPARQL Endpoint :3030</span></div>
    }
  </div>

  <div id="drop" [class.over]="over()"
       (click)="file.click()" (dragenter)="dragOn($event)" (dragover)="dragOn($event)"
       (dragleave)="dragOff($event)" (drop)="dropped($event)">
    <strong>Drop an IFC file here</strong>
    <p>or click to choose &mdash; .ifc / .ifcxml, stays on this machine</p>
    <input type="file" #file accept=".ifc,.ifcxml,.ifczip" hidden (change)="picked($event)">
  </div>

  @if (busy(); as b) {
    <div class="verdict conditional"><h3><span class="spinner"></span> Checking {{b}}</h3></div>
  }
  @if (error(); as e) {
    <div class="verdict not_ready"><h3>Could not read the file</h3><div class="meta">{{e}}</div></div>
  }
  @if (st.lastCheck(); as d) {
    <div class="verdict" [class]="'verdict '+d.level">
      <h3>{{d.verdict}}</h3>
      <div class="meta">{{d.model}} &middot; schema {{d.schema}} &middot; {{d.entities}} entities
        &middot; mandatory failed: {{d.mandatory_failed.length ? d.mandatory_failed.join(', ') : 'none'}}
        &middot; recommended score {{pct(d)}}%</div>
      <div class="bar"><i [style.width.%]="pct(d)"
        [style.background]="d.level==='not_ready'?'var(--bad)':d.level==='conditional'?'var(--warn)':'var(--ok)'"></i></div>
    </div>
    @if (gaps(d).length) {
      <p class="hint"><b>{{gaps(d).length}} gap(s) to close:</b> {{gapIds(d)}} &mdash;
        see the <a href="#" (click)="st.activeTab.set(2); $event.preventDefault()">Requirements</a> tab
        for what each one is for.</p>
    }
    <div class="scroll"><table>
      <thead><tr><th>ID</th><th>Check</th><th>Result</th></tr></thead>
      <tbody>
      @for (r of d.results; track r.id) {
        <tr>
          <td><code>{{r.id}}</code>@if (r.mandatory) {<br><span class="tag m">GATE</span>}</td>
          <td>{{r.title}}<div class="det">{{r.detail}}</div>
            <div class="src">per {{r.sources[0]}}@if (r.sources.length>1) { +{{r.sources.length-1}} more}</div></td>
          <td><span class="tag" [class.pass]="r.pass" [class.fail]="!r.pass">{{r.pass?'PASS':'FAIL'}}</span></td>
        </tr>
      }
      </tbody>
    </table></div>
    <div class="row" style="margin-top:14px">
      <button class="b" (click)="download(d)">Download report JSON</button>
      <button class="b" (click)="print()">Print / PDF</button>
    </div>
  }

  <h2>Requirements <span style="font-weight:400;color:var(--mut);font-size:13px">(generated from the graph)</span></h2>
  <div class="scroll"><table>
    <thead><tr><th>ID</th><th>Requirement</th><th>Level</th><th>Derived from</th></tr></thead>
    <tbody>
    @for (r of specRows(); track r.id) {
      <tr>
        <td><code>{{r.id}}</code></td>
        <td>{{r.title}}<div class="src">{{r.rationale}}</div></td>
        <td>@if (r.mandatory) {<span class="tag m">MANDATORY</span>} @else {weight {{r.weight||1}}}</td>
        <td class="src">@for (x of r.sources; track x.node) {{{x.standard}} {{x.clause}}<br>}</td>
      </tr>
    }
    </tbody>
  </table></div>
  <p class="hint">Same audit from the terminal:
    <code>python3 backend/audit/check_ifc_pdm.py model.ifc --json report.json</code></p>
  `,
})
export class CheckTab {
  st = inject(AppState);
  private api = inject(Api);
  kg = signal<any | null>(null);
  specRows = signal<any[]>([]);
  busy = signal<string | null>(null);
  error = signal<string | null>(null);
  over = signal(false);

  constructor() {
    this.api.kg().then(k => this.kg.set(k));
    this.api.spec().then(s => this.specRows.set(s.requirements));
  }
  pct(d: any) { return Math.round(d.recommended_score * 100); }
  gaps(d: any) { return d.results.filter((r: any) => !r.pass); }
  gapIds(d: any) { return this.gaps(d).map((g: any) => g.id).join(', '); }
  dragOn(e: DragEvent) { e.preventDefault(); this.over.set(true); }
  dragOff(e: DragEvent) { e.preventDefault(); this.over.set(false); }
  dropped(e: DragEvent) {
    e.preventDefault(); this.over.set(false);
    const f = e.dataTransfer?.files[0]; if (f) this.send(f);
  }
  picked(e: Event) {
    const f = (e.target as HTMLInputElement).files?.[0]; if (f) this.send(f);
  }
  async send(f: File) {
    this.busy.set(f.name); this.error.set(null);
    try {
      const d = await this.api.check(f);
      if (d.error) { this.error.set(d.error); this.st.lastCheck.set(null); }
      else this.st.lastCheck.set(d);
    } catch (e: any) { this.error.set(e?.message || String(e)); }
    this.busy.set(null);
  }
  download(d: any) {
    const b = new Blob([JSON.stringify(d, null, 2)], { type: 'application/json' });
    const a = document.createElement('a');
    a.href = URL.createObjectURL(b);
    a.download = 'pdm_readiness_' + d.model.replace(/[^\w.-]/g, '_') + '.json';
    a.click(); URL.revokeObjectURL(a.href);
  }
  print() { window.print(); }
}
