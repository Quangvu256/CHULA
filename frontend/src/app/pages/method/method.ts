import { DecimalPipe } from '@angular/common';
import { Component, inject, signal } from '@angular/core';
import { Api } from '../../core/api';
import { MT } from './i18n';

// (bilingual dictionary lives in ./i18n.ts)

@Component({
  selector: 'method-tab',
  template: `
  <div class="row" style="margin-bottom:10px">
    <button class="b" [class.on]="lang()==='en'" (click)="lang.set('en')">English</button>
    <button class="b" [class.on]="lang()==='vi'" (click)="lang.set('vi')">Tiếng Việt</button>
  </div>
  @if (met(); as d) {
    <p class="sub">{{T().sub}}</p>
    <div class="stats">
      @for (c of cards(d); track $index) {
        <div class="stat"><b>{{c[0] | number}}</b><span>{{c[1]}}</span></div>
      }
    </div>
    <h2>{{T().h_pipe}}</h2>
    <div class="pipe">
      @for (x of T().stages; track $index; let i = $index) {
        @if (i) {<div class="arrow">&#8594;<i [style.animation-delay]="(i*0.2)+'s'"></i></div>}
        <div class="stage" [style.animation-delay]="(i*0.15)+'s'">
          <b>{{x[0]}}</b><span>{{fill(x[1], d)}}</span>
          <span class="tag" [class.w]="x[2]==='judgment'" [class.m]="x[2]!=='judgment'"
                style="margin-top:6px;display:inline-block">{{T().tags[x[2]]}}</span></div>
      }
    </div>
    <p class="hint">{{T().hint_pipe}}</p>
    <h2>{{T().h_gates}}</h2>
    <div class="scroll" style="padding:6px 14px">
      @for (g of gates(d); track $index) {
        <div class="meterrow">
          <span><b>{{g.name}}</b><br><span class="src">{{g.desc}}</span><br>
            <span class="src det">{{g.formula}}</span></span>
          <div class="meter"><i [style.width.%]="armed() ? g.pct : 0"></i></div>
          <span class="val">{{g.val}}</span></div>
      }
    </div>
    <h2>{{T().h_bench}}</h2>
    <p class="hint" style="margin-top:0">{{T().hint_bench}}</p>
    <div class="scroll" style="padding:6px 14px">
      @for (r of bench(d); track r.part) {
        <div class="meterrow">
          <span><b>{{r.part}}</b><br><span class="src">{{T().termfid}}</span><br>
            <span class="src det">{{T().fprec}} = {{r.createdMatched}} / {{r.created}} = {{r.tp}}%<br>
            {{T().frec}} = {{r.termFound}} / {{r.goldTerms}} = {{r.tr}}%</span></span>
          <div class="meter"><i [style.width.%]="armed() ? r.tr : 0"></i></div>
          <span class="val">{{r.tp}}% &middot; {{r.tr}}%</span></div>
        <div class="meterrow">
          <span><span class="src">{{T().reach}}</span><br>
            <span class="src det">{{T().freach}} = {{r.found}} / {{r.goldNames}} = {{r.rc}}%</span></span>
          <div class="meter"><i class="acc" [style.width.%]="armed() ? r.rc : 0"></i></div>
          <span class="val">{{r.rc}}% ({{r.found}}/{{r.goldNames}})</span></div>
      }
    </div>
    <p class="hint">{{benchNote(d)}}</p>
  }`,
  imports: [DecimalPipe],
})
export class MethodTab {
  private api = inject(Api);
  met = signal<any | null>(null);
  lang = signal<'en' | 'vi'>('en');
  armed = signal(false);
  constructor() {
    this.api.method().then(d => { this.met.set(d); setTimeout(() => this.armed.set(true), 150); });
  }
  T() { return MT[this.lang()]; }
  fill(t: string, d: any) {
    return t.replace('NODES', d.nodes).replace('RELS', d.rels).replace('PARTS', d.parts.length);
  }
  cards(d: any): [number, string][] {
    const m = d.metrics || {}, L = this.T().cards;
    const v = [d.parts.length, d.nodes, d.rels, m.E3_provenances_checked || 0, d.uc_edges, d.conflicts];
    return v.map((x, i) => [x, L[i]] as [number, string]);
  }
  gates(d: any) {
    const T = this.T(), m = d.metrics || {};
    const e2t = m.E2_terms_total || 0, e2v = m.E2_terms_verbatim || 0,
          e2n = m.E2_terms_near || 0, e2f = m.E2_terms_failed || 0;
    const e3c = m.E3_provenances_checked || 0, e3u = m.E3_unresolved || 0;
    const cov = (m.E5_term_coverage || '0/0').split('/');
    return [
      { name: T.gates[0][0], desc: T.gates[0][1], pct: m.E1_structural_pass ? 100 : 0,
        formula: `${T.fviol} = 0 → ${m.E1_structural_pass ? T.fpass : 'FAIL'}`,
        val: m.E1_structural_pass ? T.fpass : 'FAIL' },
      { name: T.gates[1][0], desc: T.gates[1][1],
        pct: e2t ? Math.round(100 * (e2t - e2f) / e2t) : 0,
        formula: `${T.fdel} = (${e2v} + ${e2n}) / ${e2t} = ${e2t ? Math.round(100 * (e2v + e2n) / e2t) : 0}%`,
        val: `${e2v} + ${e2n} / ${e2t}` },
      { name: T.gates[2][0], desc: T.gates[2][1],
        pct: e3c ? Math.round(100 * (e3c - e3u) / e3c) : 0,
        formula: `${T.fval} = ${(e3c - e3u).toLocaleString()} / ${e3c.toLocaleString()} = ${e3c ? Math.round(100 * (e3c - e3u) / e3c) : 0}%`,
        val: `${(e3c - e3u).toLocaleString()} / ${e3c.toLocaleString()}` },
      { name: T.gates[3][0], desc: T.gates[3][1], pct: m.E4_traversability_pass ? 100 : 0,
        formula: `spine ${m.E4_spine || '?'} · high-PdM ${m.E4_high_pdm_reachable || '?'}`,
        val: m.E4_traversability_pass ? T.fpass : 'FAIL' },
      { name: T.gates[4][0], desc: T.gates[4][1], pct: 100,
        formula: `${T.fcov} = ${cov[0]} / ${cov[1]} = ${Math.round(100 * +cov[0] / +cov[1])}%`,
        val: m.E5_term_coverage || '' },
    ];
  }
  bench(d: any) {
    return d.benchmark.rows.map((r: any) => ({ ...r,
      tp: Math.round(100 * r.createdMatched / r.created),
      tr: Math.round(100 * r.termFound / r.goldTerms),
      rc: Math.round(100 * r.found / r.goldNames) }));
  }
  benchNote(d: any) {
    return this.lang() === 'vi'
      ? `Benchmark ngày ${d.benchmark.date}: máy sinh bản nháp v2 chấm so với 4 file gold; chuẩn của chính file gold bị loại khỏi registry để bộ resolve không thể tự gian lận. Ghi chú mẫu số: goldNames đếm tên node duy nhất sau khi chuẩn hoá hậu tố, nên Part 6 hiện 86 cho file 90 node.`
      : `Benchmark of ${d.benchmark.date}: ${d.benchmark.note} ${d.benchmark.denominator_note || ''}`;
  }
}
