import { Component, inject, signal } from '@angular/core';
import { NgTemplateOutlet } from '@angular/common';
import { Api } from '../../core/api';
import { AppState } from '../../core/state';

@Component({
  selector: 'requirements-tab',
  template: `
  @if (spec(); as s) {
    <div class="callout"><h3>{{s.use_case}}</h3>
      <p style="margin-bottom:0">Acceptance criteria for an IFC model feeding this use case. In
      ISO 19650 terms this is EIR-level content. Derived from
      @for (f of s.derived_from; track f) {<code>{{f}}</code> }.</p></div>

    <div class="callout"><h3>How these {{s.requirements.length}} requirements are produced</h3>
      <p>{{s.how_generated}}</p>
      <p style="margin-bottom:0"><b>They are not the use case.</b> The use case lives in the graph and
      describes the running loop (sensor &rarr; model &rarr; alert &rarr; work order &rarr; outcome).
      These requirements are its projection onto one deliverable: what an IFC file must contain for
      that loop to bind to it. Runtime artefacts such as the alert or the work order are deliberately
      absent &mdash; they are produced during operation, not found in a handover model.
      See the <a href="#" (click)="st.activeTab.set(3); $event.preventDefault()">Explore graph</a>
      tab for the use case itself.</p></div>

    <div class="callout"><h3>How a verdict is decided</h3>
      @for (kv of verdictRules(s); track kv[0]) {
        <div class="rule"><span>{{kv[0]}}</span><span>{{kv[1]}}</span></div>
      }
      <p class="hint" style="margin:8px 0 0">{{gates(s).length}} gates, {{scored(s).length}} scored
        requirements, total weight {{totalWeight(s)}}.</p></div>

    <div class="callout"><h3>Normative or informative?</h3>
      <p style="margin-bottom:0">{{s.modality_note}}</p>
      <div style="margin-top:8px"><span class="mod normative">normative</span>
        <span class="mod informative">informative</span>
        <span class="mod mixed">mixed</span> &mdash; shown on every clause below.</div></div>

    <div class="row" style="margin:14px 0 6px">
      <button class="b" (click)="setAll(true)">Expand all</button>
      <button class="b" (click)="setAll(false)">Collapse all</button>
      @if (st.lastCheck(); as d) {
        <span class="hint">showing the result of the last check: {{d.model}}</span>
      }
    </div>

    <div class="tree" #tree>
      <details class="grp" open><summary>Mandatory gates
        <small>&mdash; {{gates(s).length}} &middot; fail any one and the model cannot join the twin</small></summary>
        @for (r of gates(s); track r.id) { <ng-container *ngTemplateOutlet="node; context: {r}"/> }
      </details>
      <details class="grp" open><summary>Scored requirements
        <small>&mdash; {{scored(s).length}} &middot; total weight {{totalWeight(s)}} &middot; each one unlocks more of the loop</small></summary>
        @for (r of scored(s); track r.id) { <ng-container *ngTemplateOutlet="node; context: {r}"/> }
      </details>
    </div>

    <ng-template #node let-r="r">
      <details class="node"><summary>
        <code>{{r.id}}</code>
        @if (passOf(r.id); as p) {
          <span class="tag" [class.pass]="p==='PASS'" [class.fail]="p==='FAIL'">{{p}}</span>
        }
        <b>{{r.title}}</b>
        <span class="mod" [class]="'mod '+r.basis">{{r.basis}}</span>
        <span class="cat">{{r.category}}</span>
        @if (!r.mandatory) {<span class="cat">w{{r.weight||1}}</span>}</summary>
       <div class="fields">
         <div class="f"><span>Serves</span><span>{{r.loop_step}}</span></div>
         <div class="f"><span>Why it exists</span><span>{{r.rationale}}</span></div>
         <div class="f"><span>Without it</span><span>{{r.if_missing}}</span></div>
         <div class="f"><span>Checker looks for</span><span class="det">{{r.probe_human}}</span></div>
         @if (detailOf(r.id); as det) {
           <div class="f"><span>Last check</span><span class="det">{{det}}</span></div>
         }
         <details class="node" style="margin-left:0"><summary>
           <span>Basis &mdash; {{r.sources.length}} clause(s) ({{modSummary(r)}})</span></summary>
           <div style="margin-left:19px">
           @for (x of r.sources; track x.node) {
             <div class="cite">
               <b>{{x.name}}</b> <span class="mod" [class]="'mod '+x.modality">{{x.modality}}</span>
               <div class="src">{{x.standard}}, clause {{x.clause}}
                 &middot; <code>{{x.node}}</code> &middot; PdM {{x.pdm_relevance}}</div>
               <div class="src" style="margin-top:4px">{{x.definition}}</div>
               <a href="#" (click)="st.gotoNode(x.node); $event.preventDefault()">show in graph &rarr;</a>
             </div>
           }
           </div></details>
       </div></details>
    </ng-template>
  }`,
  imports: [NgTemplateOutlet],
})
export class RequirementsTab {
  st = inject(AppState);
  private api = inject(Api);
  spec = signal<any | null>(null);
  constructor() { this.api.spec().then(s => this.spec.set(s)); }
  gates(s: any) { return s.requirements.filter((r: any) => r.mandatory); }
  scored(s: any) { return s.requirements.filter((r: any) => !r.mandatory); }
  totalWeight(s: any) { return this.scored(s).reduce((a: number, r: any) => a + (r.weight || 1), 0); }
  verdictRules(s: any): [string, string][] {
    return Object.entries(s.verdict_rule).map(([k, v]) => [k.replace('_', '-').toUpperCase(), v as string]);
  }
  modSummary(r: any) {
    const m: Record<string, number> = {};
    r.sources.forEach((x: any) => m[x.modality] = (m[x.modality] || 0) + 1);
    return Object.entries(m).map(([k, v]) => `${v} ${k}`).join(', ');
  }
  passOf(id: string): string | null {
    const d = this.st.lastCheck(); if (!d) return null;
    const r = d.results.find((x: any) => x.id === id);
    return r ? (r.pass ? 'PASS' : 'FAIL') : null;
  }
  detailOf(id: string): string | null {
    const d = this.st.lastCheck(); if (!d) return null;
    return d.results.find((x: any) => x.id === id)?.detail ?? null;
  }
  setAll(open: boolean) {
    document.querySelectorAll('requirements-tab details').forEach(d => (d as HTMLDetailsElement).open = open);
  }
}
