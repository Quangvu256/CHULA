import { AfterViewInit, Component, ElementRef, HostListener, OnDestroy, ViewChild,
         effect, inject, signal } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Api } from '../../core/api';
import { AppState } from '../../core/state';

/** W3C RDF Triples (.ttl) Canvas Graph Explorer.
 *  Visual layout matches the W3C RDF Triple Store diagram:
 *  Subject (Circle Node with double rim) ---> [ Predicate Box ] ---> Object (Resource / Literal Node).
 *  The physics engine is the deterministic settle engine ported verbatim from BIMLab_KG:
 *  phyllotaxis seed (no Math.random), monotonic alpha decay rendered over ~90 frames, then a dead stop.
 */
const USECASE_CORE = [
  'term_asset', 'term_condition_monitoring_system', 'term_health_indicator',
  'term_anomaly_event', 'term_remaining_useful_life_prediction', 'term_maintenance_alert',
  'term_maintenance_work_order', 'term_failure_mode', 'term_asset_criticality',
  'term_asset_operational_data', 'term_pdm_model', 'term_hs_risk', 'term_treatment_control'
];

const USECASE = [
  ...USECASE_CORE,
  'term_scada_system', 'term_condition_observation', 'term_maintenance_intervention_outcome',
  'term_asset_failure_history', 'term_maintenance_history', 'term_asset_condition_duty',
  'term_hs_incident', 'term_near_miss', 'term_risk_treatment', 'term_level_of_risk',
  'term_likelihood', 'term_consequence', 'term_risk_urgency_prioritization',
  'term_hs_register', 'term_hs_properties', 'term_foreseen_trigger_event',
  'trigger_maintenance_work', 'term_security_information_requirements', 'term_aim'
];

const PCOL: Record<string, string> = {
  'ISO 19650-1': '--p1',
  'ISO 19650-2': '--p2',
  'ISO 19650-3': '--p3',
  'ISO 19650-4': '--p4',
  'ISO 19650-5': '--p5',
  'ISO 19650-6': '--p6'
};

const SIM = { CH: -5200, LD: 240, LS: 0.08, GR: 0.015, VD: 0.65, VMAX: 32 };

@Component({
  selector: 'graph-tab',
  standalone: true,
  imports: [CommonModule, FormsModule],
  template: `
  <div class="gbar">
    <strong style="font-size:13px; color: var(--acc)">W3C RDF Triple Store:</strong>
    <button class="b" [class.on]="view()==='core'" (click)="preset('core')">PdM Core (13 nodes)</button>
    <button class="b" [class.on]="view()==='usecase'" (click)="preset('usecase')">PdM Full (32 nodes)</button>
    <button class="b" [class.on]="view()==='high'" (click)="preset('high')">High-PdM only</button>
    <button class="b" [class.on]="view()==='all'" (click)="preset('all')">Everything</button>
    <button class="b" [class.on]="paletteMode()==='protege'" (click)="togglePalette()" title="Switch between Protégé OWL Taxonomy shapes/colors and ISO Part colors">
      Theme: {{paletteMode()==='protege' ? 'Protégé OWL' : 'ISO Parts'}}
    </button>
  </div>
  <div class="gbar">
    <input type="search" placeholder="Search Subject, Predicate, or Object&hellip;" [value]="q()"
           (input)="q.set($any($event.target).value); rebuild(false)">
    <span>
      @for (p of partKeys; track p) {
        <label><input type="checkbox" [checked]="!hidden().has(p)" (change)="togglePart(p)">
          <span class="dot" [style.background]="'var('+pcol[p]+')'"></span>{{p.replace('ISO 19650-','P')}}</label>
      }
    </span>
    <label title="Clicking a node hides everything that is not connected to it">
      <input type="checkbox" #focusBox> focus on click</label>
    <button class="b" (click)="fit()">Fit</button>
    <button class="b" (click)="rebuild(true)">Re-layout</button>
    <button class="b" (click)="toggleFS()">&#x26F6; Fullscreen</button>
    @if (focusId()) {<button class="b" (click)="unfocus()">&larr; Back</button>}
    <span class="hint">{{count()}}</span>
  </div>
  <div class="gwrap" #gwrap [class.fs]="fs()">
    <div id="fsbar">
      <button class="b" (click)="fit()">Fit</button>
      @if (focusId()) {<button class="b" (click)="unfocus()">&larr; Back</button>}
      <button class="b" (click)="toggleFS()">&#x2715; Exit (Esc)</button>
    </div>
    <canvas #cv id="cv"
      (mousedown)="onDown($event)" (mousemove)="onMove($event)" (dblclick)="onDbl($event)"
      (wheel)="onWheel($event)"></canvas>
    <div id="panel" [class.show]="fs() && !!selected()">
      @if (selected(); as n) {
        <button class="pclose" (click)="hidePanel()" title="close">&#x2715;</button>
        <h3>
          @if (getNodeKind(n) === 'class') {<span style="color:#f59e0b; font-size:16px" title="OWL Class">●</span>}
          @else if (getNodeKind(n) === 'individual') {<span style="color:#a855f7; font-size:16px" title="OWL Individual">◆</span>}
          @else {<span style="color:#10b981; font-size:16px" title="Literal Value">■</span>}
          {{n.name}}
        </h3>
        <div class="src"><span class="dot" [style.background]="'var('+(pcol[n.part]||'--mut')+')'"></span>
          {{n.part}} &middot; {{n.label}} &middot; <code>{{n.id}}</code></div>
        
        <div class="k" style="color: #f59e0b; display:flex; align-items:center; gap:4px">
          <span style="color:#f59e0b; font-size:14px">●</span> Types (Class Taxonomy)
        </div>
        <div class="src" style="display:flex; align-items:center; gap:6px; background: rgba(245,158,11,0.1); padding: 4px 8px; border-radius: 4px; border: 1px solid rgba(245,158,11,0.3); color: #f59e0b">
          <span style="color:#f59e0b; font-size:14px">●</span> <b>{{n.label}}</b> &middot; <code>iso:IsoNode</code>
        </div>

        <div class="k" style="color: #38bdf8; margin-top:8px">W3C RDF Turtle (.ttl)</div>
        <div class="src" style="font-family: monospace; background: rgba(15,23,42,0.6); padding: 6px; border-radius: 4px; overflow-x: auto; color: #38bdf8">
          iso:{{n.id}} a iso:{{n.label}} ;<br>
          &nbsp;&nbsp;rdfs:label "{{n.name}}" ;<br>
          &nbsp;&nbsp;iso:part "{{n.part}}" .
        </div>

        <div class="row" style="margin-top:10px">
          <button class="b" (click)="focusOn(n.id)">Show only this neighbourhood</button>
        </div>

        <div class="k" style="color: #10b981; display:flex; align-items:center; gap:4px">
          <span style="color:#10b981; font-size:14px">■</span> Data property assertions
        </div>
        <div style="font-size:13px">{{n.def}}</div>
        <div class="src" style="margin-top:2px">Provenance: {{n.std}} &mdash; clause {{n.cl}}</div>
        @if (n.note) {<div class="src" style="font-size:12px; margin-top:2px">Note: {{n.note}}</div>}

        <div class="k" style="color: #38bdf8; display:flex; align-items:center; gap:4px; margin-top:10px">
          <span style="color:#38bdf8; font-size:14px">■</span> Object property assertions (Outgoing {{outEdges().length}})
        </div>
        @for (e of outEdges(); track $index) {
          <div class="nb" (click)="jump(e.t)">
            <span style="color:#38bdf8; font-weight:bold">■</span>
            &rarr; <b>[{{e.type}}]</b> {{nodeOf(e.t)?.name || e.t}}
            <div class="src">{{e.std}} {{e.cl}}</div></div>
        } @empty {<div class="src">none</div>}

        <div class="k" style="color: #38bdf8; display:flex; align-items:center; gap:4px; margin-top:10px">
          <span style="color:#38bdf8; font-size:14px">■</span> Object property assertions (Incoming {{inEdges().length}})
        </div>
        @for (e of inEdges(); track $index) {
          <div class="nb" (click)="jump(e.s)">
            <span style="color:#38bdf8; font-weight:bold">■</span>
            &larr; <b>[{{e.type}}]</b> {{nodeOf(e.s)?.name || e.s}}
            <div class="src">{{e.std}} {{e.cl}}</div></div>
        } @empty {<div class="src">none</div>}
      } @else if (!fs()) {
        <p class="hint">Click a Subject or Object node to read its Protégé RDF Turtle triples, Predicates, and Literals.
        Drag to move a node, scroll to zoom, drag background to pan.</p>
      }
    </div>
  </div>
  <div class="legend">
    @if (paletteMode() === 'protege') {
      <span style="font-weight:600; color:var(--acc)">Protégé Taxonomy:</span>
      <span><span style="color:#f59e0b; font-size:14px; margin-right:3px">●</span> OWL Class</span>
      <span><span style="color:#a855f7; font-size:14px; margin-right:3px">◆</span> Individual / Subject</span>
      <span><span style="color:#38bdf8; font-size:14px; margin-right:3px">■</span> Object Property</span>
      <span><span style="color:#10b981; font-size:14px; margin-right:3px">■</span> Data Property / Literal</span>
    } @else {
      @for (p of partKeys; track p) {
        <span><span class="dot" [style.background]="'var('+pcol[p]+')'"></span>{{p}}</span>
      }
    }
    <span>node size = connections</span>
    <span style="margin-left: auto; color: var(--acc)">Protégé RDF Triple Store Visualization</span>
  </div>`,
})
export class GraphTab implements AfterViewInit, OnDestroy {
  st = inject(AppState);
  private api = inject(Api);
  @ViewChild('cv') cvRef!: ElementRef<HTMLCanvasElement>;
  @ViewChild('gwrap') gwrapRef!: ElementRef<HTMLDivElement>;
  @ViewChild('focusBox') focusBox!: ElementRef<HTMLInputElement>;

  pcol = PCOL;
  partKeys = Object.keys(PCOL);
  view = signal('core');
  q = signal('');
  hidden = signal(new Set<string>());
  focusId = signal<string | null>(null);
  selected = signal<any | null>(null);
  count = signal('');
  fs = signal(false);
  paletteMode = signal<'protege' | 'iso'>('protege');

  private G: any = null;
  private byId: Record<string, any> = {};
  private N: any[] = [];
  private E: any[] = [];
  private ctx!: CanvasRenderingContext2D;
  private W = 0; private H = 0; private scale = 1; private tx = 0; private ty = 0;
  private simAlpha = 0; private anim = 0;
  private drag: any = null; private pan: any = null; private hover: any = null;
  private moved = false; private userMoved = false;
  private ro?: ResizeObserver;

  constructor() {
    effect(() => {
      const id = this.st.pendingFocus();
      if (id && this.G) { this.st.pendingFocus.set(null); this.showNode(id); }
    });
  }

  ngAfterViewInit() {
    this.ctx = this.cvRef.nativeElement.getContext('2d')!;
    this.ro = new ResizeObserver(() => {
      const r = this.cvRef.nativeElement.getBoundingClientRect();
      if (r.width < 5 || r.height < 5) return;
      this.resize();
      if (!this.userMoved) this.fit(); else this.draw();
    });
    this.ro.observe(this.cvRef.nativeElement);
    this.loadGraphData();
    document.addEventListener('fullscreenchange', this.onFsChange);
    (document as any).addEventListener('webkitfullscreenchange', this.onFsChange);
  }

  ngOnDestroy() {
    this.ro?.disconnect();
    cancelAnimationFrame(this.anim);
    document.removeEventListener('fullscreenchange', this.onFsChange);
    (document as any).removeEventListener('webkitfullscreenchange', this.onFsChange);
  }

  private loadGraphData() {
    const handleData = (g: any) => {
      if (!g || !g.nodes || !g.nodes.length) return false;
      this.G = g;
      this.byId = {};
      g.nodes.forEach((n: any) => this.byId[n.id] = n);
      this.resize();
      this.rebuild(true);
      const id = this.st.pendingFocus();
      if (id) { this.st.pendingFocus.set(null); this.showNode(id); }
      return true;
    };

    this.api.graphRdf().then(g => {
      if (!handleData(g)) {
        this.api.graph().then(handleData);
      }
    }).catch(() => {
      this.api.graph().then(handleData);
    });
  }

  private cssv(v: string) { return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }
  nodeOf(id: string) { return this.byId[id]; }
  outEdges() { const s = this.selected(); return s ? this.E.filter(e => e.s === s.id) : []; }
  inEdges() { const s = this.selected(); return s ? this.E.filter(e => e.t === s.id) : []; }

  getNodeKind(n: any): 'class' | 'individual' | 'literal' {
    if (!n) return 'individual';
    if (n.kind === 'literal' || n.label === 'Literal') return 'literal';
    if (n.kind === 'class' ||
        ['Class', 'IsoNode', 'ISO Node', 'owl:Class', 'Concept', 'Function', 'Perspective', 'Principle', 'Process', 'Purpose', 'Requirement', 'State', 'WorkflowPhase', 'Workflow Phase'].includes(n.label) ||
        ['IsoNode', 'Concept', 'Function', 'Perspective', 'Principle', 'Process', 'Purpose', 'Requirement', 'State', 'WorkflowPhase'].includes(n.id)) {
      return 'class';
    }
    return 'individual';
  }

  togglePalette() {
    this.paletteMode.set(this.paletteMode() === 'protege' ? 'iso' : 'protege');
    this.draw();
  }

  showNode(id: string) {
    const n = this.byId[id]; if (!n) return;
    this.q.set(n.name); this.view.set('');
    this.rebuild(true);
    setTimeout(() => { const m = this.N.find(x => x.id === id); if (m) this.select(m); }, 100);
  }
  preset(v: string) { this.view.set(v); this.focusId.set(null); this.q.set(''); this.rebuild(true); }
  togglePart(p: string) {
    const h = new Set(this.hidden()); h.has(p) ? h.delete(p) : h.add(p);
    this.hidden.set(h); this.rebuild(true);
  }
  focusOn(id: string) { this.focusId.set(id); this.rebuild(true);
    setTimeout(() => { const m = this.N.find(x => x.id === id); if (m) this.select(m); }, 60); }
  unfocus() { this.focusId.set(null); this.rebuild(true); }
  hidePanel() { this.selected.set(null); this.draw(); }

  rebuild(relayout: boolean) {
    if (!this.G) return;
    const q = this.q().trim().toLowerCase();
    const focusId = this.focusId();
    const taxonomyClassIds = new Set(['IsoNode', 'Concept', 'Function', 'Perspective', 'Principle', 'Process', 'Purpose', 'Requirement', 'State', 'WorkflowPhase']);
    let keep: Set<string>;
    if (focusId) {
      keep = new Set([focusId]);
      this.G.edges.forEach((e: any) => { if (e.s === focusId) keep.add(e.t); if (e.t === focusId) keep.add(e.s); });
    } else if (this.view() === 'core') {
      keep = new Set(USECASE_CORE.filter(s => this.byId[s]));
    } else if (this.view() === 'usecase') {
      keep = new Set(USECASE.filter(s => this.byId[s]));
    } else if (this.view() === 'high') {
      keep = new Set(this.G.nodes.filter((n: any) => n.pdm === 'high').map((n: any) => n.id));
    } else {
      keep = new Set(this.G.nodes.map((n: any) => n.id));
    }
    if (q && !focusId) {
      const hit = new Set(this.G.nodes
        .filter((n: any) => n.name.toLowerCase().includes(q) || n.id.includes(q)).map((n: any) => n.id));
      const grow = new Set(hit);
      this.G.edges.forEach((e: any) => { if (hit.has(e.s)) grow.add(e.t); if (hit.has(e.t)) grow.add(e.s); });
      keep = grow as Set<string>;
    }

    // Keep connected yellow OWL Class nodes for active individuals
    const extraClasses = new Set<string>();
    this.G.edges.forEach((e: any) => {
      if (keep.has(e.s) && taxonomyClassIds.has(e.t)) extraClasses.add(e.t);
      if (keep.has(e.t) && taxonomyClassIds.has(e.s)) extraClasses.add(e.s);
    });
    extraClasses.forEach(c => keep.add(c));
    const old: Record<string, any> = {}; this.N.forEach(n => old[n.id] = n);
    const hidden = this.hidden();
    this.N = this.G.nodes.filter((n: any) => keep.has(n.id) && !hidden.has(n.part)).map((n: any) => {
      const p = !relayout && old[n.id];
      return { ...n, x: p ? p.x : 0, y: p ? p.y : 0, vx: 0, vy: 0, deg: 0, pin: p ? p.pin : false };
    });
    const ids = new Set(this.N.map(n => n.id)); const pos: Record<string, any> = {};
    this.N.forEach(n => pos[n.id] = n);
    this.E = this.G.edges.filter((e: any) => ids.has(e.s) && ids.has(e.t))
      .map((e: any) => ({ ...e, a: pos[e.s], b: pos[e.t] }));
    this.E.forEach(e => { e.a.deg++; e.b.deg++; });
    this.count.set(`${this.N.length} RDF nodes, ${this.E.length} triples`
      + (focusId ? ` (focused on ${this.byId[focusId].name})` : ''));
    if (relayout) { this.seed(); this.userMoved = false;
      this.selected.set(focusId ? this.N.find(n => n.id === focusId) || null : null);
      this.settle(this.N.length > 200 ? 760 : 520); }
    else { this.fit(); }
  }

  private seed() {
    const A = Math.PI * (3 - Math.sqrt(5));
    this.N.forEach((n, i) => { const r = 38 * Math.sqrt(0.5 + i), a = i * A;
      n.x = r * Math.cos(a); n.y = r * Math.sin(a); n.vx = 0; n.vy = 0; });
  }
  private tickOnce() {
    const n = this.N.length, { CH, LD, LS, GR, VD, VMAX } = SIM; if (!n) return;
    for (let i = 0; i < n; i++) { const a = this.N[i];
      for (let j = i + 1; j < n; j++) { const b = this.N[j];
        let dx = b.x - a.x, dy = b.y - a.y, d2 = dx * dx + dy * dy;
        if (d2 < 36) { dx = dx || (i % 2 ? 0.9 : -0.9); dy = dy || 0.9; d2 = 36; }
        if (d2 > 360000) continue;
        const w = CH * this.simAlpha / d2;
        a.vx += dx * w; a.vy += dy * w; b.vx -= dx * w; b.vy -= dy * w; } }
    for (const e of this.E) {
      const dx = e.b.x - e.a.x, dy = e.b.y - e.a.y, d = Math.hypot(dx, dy) || 1;
      const w = (d - LD) / d * this.simAlpha * LS;
      e.a.vx += dx * w; e.a.vy += dy * w; e.b.vx -= dx * w; e.b.vy -= dy * w; }
    for (const a of this.N) {
      a.vx -= a.x * GR * this.simAlpha; a.vy -= a.y * GR * this.simAlpha;
      a.vx *= VD; a.vy *= VD;
      const sp = Math.hypot(a.vx, a.vy);
      if (sp > VMAX) { a.vx = a.vx / sp * VMAX; a.vy = a.vy / sp * VMAX; }
      if (a.pin || a === this.drag) continue;
      a.x += a.vx; a.y += a.vy; }
  }
  private settle(ticks: number) {
    cancelAnimationFrame(this.anim);
    this.simAlpha = 1;
    const decay = Math.pow(0.0015, 1 / ticks);
    let left = ticks;
    const per = Math.max(1, Math.ceil(ticks / 90));
    const go = () => {
      if (this.W < 5) { this.anim = requestAnimationFrame(go); return; }
      for (let k = 0; k < per && left > 0; k++) { this.tickOnce(); this.simAlpha *= decay; left--; }
      if (!this.userMoved) this.fit(); else this.draw();
      if (left > 0) this.anim = requestAnimationFrame(go);
      else { this.N.forEach(a => { a.vx = a.vy = 0; }); this.simAlpha = 0;
             if (!this.userMoved) this.fit(); else this.draw(); } };
    this.anim = requestAnimationFrame(go);
  }

  @HostListener('window:resize') onResize() { this.resize(); this.draw(); }
  private resize() {
    const cv = this.cvRef.nativeElement, r = cv.getBoundingClientRect(), dpr = devicePixelRatio || 1;
    cv.width = Math.max(1, r.width * dpr); cv.height = Math.max(1, r.height * dpr);
    this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0); this.W = r.width; this.H = r.height;
  }
  fit() {
    this.userMoved = false;
    if (!this.N.length) { this.ctx.clearRect(0, 0, this.W, this.H); return; }
    const xs = this.N.map(n => n.x), ys = this.N.map(n => n.y);
    const x0 = Math.min(...xs), x1 = Math.max(...xs), y0 = Math.min(...ys), y1 = Math.max(...ys);
    this.scale = Math.min(this.W / (x1 - x0 + 170), this.H / (y1 - y0 + 120), 2.0) || 1;
    this.tx = this.W / 2 - (x0 + x1) / 2 * this.scale;
    this.ty = this.H / 2 - (y0 + y1) / 2 * this.scale;
    this.draw();
  }
  private rad(n: any) { return 6 + Math.min(9, Math.sqrt(n.deg || 1) * 2.1); }

  private drawShape(ctx: CanvasRenderingContext2D, kind: string, X: number, Y: number, r: number) {
    ctx.beginPath();
    if (kind === 'class') {
      ctx.arc(X, Y, r, 0, Math.PI * 2);
    } else if (kind === 'individual') {
      ctx.moveTo(X, Y - r * 1.3);
      ctx.lineTo(X + r * 1.3, Y);
      ctx.lineTo(X, Y + r * 1.3);
      ctx.lineTo(X - r * 1.3, Y);
      ctx.closePath();
    } else { // literal
      const w = r * 2.2, h = r * 1.5;
      if ((ctx as any).roundRect) {
        (ctx as any).roundRect(X - w / 2, Y - h / 2, w, h, 4);
      } else {
        ctx.rect(X - w / 2, Y - h / 2, w, h);
      }
    }
  }

  private draw() {
    const ctx = this.ctx; if (!ctx) return;
    const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
    ctx.clearRect(0, 0, this.W, this.H);
    const sel = this.selected();
    const nbr = sel ? new Set(this.E.filter(e => e.s === sel.id || e.t === sel.id)
      .flatMap(e => [e.s, e.t])) : null;
    const isProtege = this.paletteMode() === 'protege';

    // 1. Draw RDF Directed Arrows & Predicate Label Boxes (Protégé Blue Object Property / Green Data Property)
    for (const e of this.E) {
      const on = sel && (e.s === sel.id || e.t === sel.id);
      const x1 = e.a.x * this.scale + this.tx;
      const y1 = e.a.y * this.scale + this.ty;
      const x2 = e.b.x * this.scale + this.tx;
      const y2 = e.b.y * this.scale + this.ty;

      const targetKind = this.getNodeKind(e.b);
      const isDataProperty = targetKind === 'literal' || e.type.startsWith('iso:def') || e.type.includes('Clause');

      ctx.lineWidth = on ? 2.2 : 1.2;
      if (isProtege) {
        ctx.strokeStyle = on ? this.cssv('--acc') : (isDataProperty ? (isDark ? '#059669' : '#16a34a') : (isDark ? '#0284c7' : '#2563eb'));
      } else {
        ctx.strokeStyle = on ? this.cssv('--acc') : this.cssv('--edge');
      }
      ctx.globalAlpha = sel ? (on ? 0.95 : 0.15) : 0.65;

      // Arrow Edge Line
      ctx.beginPath();
      ctx.moveTo(x1, y1);
      ctx.lineTo(x2, y2);
      ctx.stroke();

      // Arrowhead pointing to Object Node
      const nodeR = this.rad(e.b) * Math.min(1.5, Math.max(0.6, this.scale));
      const angle = Math.atan2(y2 - y1, x2 - x1);
      const arrowX = x2 - (nodeR + 4) * Math.cos(angle);
      const arrowY = y2 - (nodeR + 4) * Math.sin(angle);
      const headlen = 7;

      ctx.beginPath();
      ctx.moveTo(arrowX, arrowY);
      ctx.lineTo(arrowX - headlen * Math.cos(angle - Math.PI / 6), arrowY - headlen * Math.sin(angle - Math.PI / 6));
      ctx.lineTo(arrowX - headlen * Math.cos(angle + Math.PI / 6), arrowY - headlen * Math.sin(angle + Math.PI / 6));
      ctx.fillStyle = ctx.strokeStyle;
      ctx.fill();

      // RDF Predicate Label Box in the center of the arrow line
      if (this.scale > 0.55 || on || e.a === sel || e.b === sel) {
        const mx = (x1 + x2) / 2;
        const my = (y1 + y2) / 2;
        ctx.font = '10px ui-sans-serif, -apple-system, sans-serif';
        const txt = e.type || 'predicate';
        const tw = ctx.measureText(txt).width;
        const pw = tw + 10;
        const ph = 14;

        ctx.globalAlpha = sel ? (on ? 1.0 : 0.2) : 0.92;
        ctx.fillStyle = isDark ? '#0f172a' : '#ffffff';
        ctx.fillRect(mx - pw / 2, my - ph / 2, pw, ph);

        if (isProtege) {
          ctx.strokeStyle = on ? this.cssv('--acc') : (isDataProperty ? '#10b981' : '#38bdf8');
        } else {
          ctx.strokeStyle = on ? this.cssv('--acc') : (isDark ? '#3a3a42' : '#c8c8c2');
        }
        ctx.lineWidth = 1;
        ctx.strokeRect(mx - pw / 2, my - ph / 2, pw, ph);

        if (isProtege) {
          ctx.fillStyle = on ? this.cssv('--acc') : (isDataProperty ? '#34d399' : '#38bdf8');
        } else {
          ctx.fillStyle = on ? this.cssv('--acc') : (isDark ? '#e8e8e4' : '#1a1a18');
        }
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.fillText(txt, mx, my);
      }
    }

    // 2. Draw Subject & Object Nodes with Protégé Shapes (Circle Class, Diamond Individual, Rect Literal)
    ctx.globalAlpha = 1;
    for (const a of this.N) {
      const X = a.x * this.scale + this.tx, Y = a.y * this.scale + this.ty;
      const r = this.rad(a) * Math.min(1.5, Math.max(0.6, this.scale));
      const dim = sel && nbr && !nbr.has(a.id);
      const kind = this.getNodeKind(a);
      ctx.globalAlpha = dim ? 0.2 : 1;

      if (isProtege) {
        // Outer Rim Ring with Protégé translucent halo
        let rimColor = 'rgba(168, 85, 247, 0.35)'; // Purple for individual
        if (kind === 'class') rimColor = 'rgba(245, 158, 11, 0.4)'; // Yellow for class
        else if (kind === 'literal') rimColor = 'rgba(16, 185, 129, 0.4)'; // Green for literal

        this.drawShape(ctx, kind, X, Y, r + 3.5);
        ctx.strokeStyle = rimColor;
        ctx.lineWidth = 1.5;
        ctx.stroke();

        // Fill Protégé shape
        this.drawShape(ctx, kind, X, Y, r);
        if (kind === 'class') {
          ctx.fillStyle = isDark ? '#f59e0b' : '#d97706'; // Protégé Yellow Circle
        } else if (kind === 'individual') {
          ctx.fillStyle = isDark ? '#a855f7' : '#7e22ce'; // Protégé Purple Diamond
        } else {
          ctx.fillStyle = isDark ? '#10b981' : '#15803d'; // Protégé Green Rect Tag
        }
        ctx.fill();
      } else {
        // Legacy ISO Part Part-color rendering
        ctx.beginPath(); ctx.arc(X, Y, r + 3.5, 0, 6.284);
        ctx.strokeStyle = isDark ? 'rgba(255,255,255,0.18)' : 'rgba(0,0,0,0.15)';
        ctx.lineWidth = 1.5; ctx.stroke();

        ctx.beginPath(); ctx.arc(X, Y, r, 0, 6.284);
        ctx.fillStyle = a.kind === 'literal' ? '#f59e0b' : this.cssv(PCOL[a.part] || '--mut');
        ctx.fill();
      }

      if (a === sel || a === this.hover) {
        this.drawShape(ctx, kind, X, Y, r);
        ctx.lineWidth = 2.5; ctx.strokeStyle = this.cssv('--acc'); ctx.stroke();
      }
      if (a.pin) {
        ctx.globalAlpha = dim ? 0.2 : 0.6;
        this.drawShape(ctx, kind, X, Y, r + 5.5);
        ctx.strokeStyle = this.cssv('--mut'); ctx.stroke();
      }

      if (!dim && (this.scale > 0.6 || a === sel || a === this.hover || this.N.length < 50)) {
        ctx.globalAlpha = 0.95; ctx.fillStyle = this.cssv('--fg');
        ctx.font = '11px ui-sans-serif,-apple-system,sans-serif'; ctx.textAlign = 'center';
        ctx.textBaseline = 'alphabetic';
        const t = a.name.length > 30 ? a.name.slice(0, 29) + '...' : a.name;
        const offsetY = kind === 'individual' ? Y - r * 1.3 - 5 : (kind === 'literal' ? Y - r * 0.9 - 5 : Y - r - 6);
        ctx.fillText(t, X, offsetY);
      }
    }
    ctx.globalAlpha = 1;
  }

  private at(ev: MouseEvent) {
    const r = this.cvRef.nativeElement.getBoundingClientRect();
    const mx = ev.clientX - r.left, my = ev.clientY - r.top;
    let best: any = null, bd = 1e9;
    for (const a of this.N) {
      const dx = a.x * this.scale + this.tx - mx, dy = a.y * this.scale + this.ty - my;
      const d = dx * dx + dy * dy;
      const rr = this.rad(a) * Math.min(1.5, Math.max(0.6, this.scale)) + 8;
      if (d < bd && d < rr * rr) { bd = d; best = a; } }
    return { n: best, mx, my };
  }
  onDown(ev: MouseEvent) {
    const { n, mx, my } = this.at(ev); this.moved = false;
    if (n) { this.drag = n; this.select(n); }
    else { this.pan = { mx, my, tx: this.tx, ty: this.ty };
           this.userMoved = true; this.cvRef.nativeElement.classList.add('drag'); }
  }
  onMove(ev: MouseEvent) {
    const r = this.cvRef.nativeElement.getBoundingClientRect();
    if (this.drag) {
      this.moved = true;
      this.drag.x = (ev.clientX - r.left - this.tx) / this.scale;
      this.drag.y = (ev.clientY - r.top - this.ty) / this.scale;
      this.drag.pin = true; this.simAlpha = 0.10; this.tickOnce(); this.simAlpha = 0;
      this.draw(); return; }
    if (this.pan) {
      this.moved = true; this.userMoved = true;
      this.tx = this.pan.tx + (ev.clientX - r.left - this.pan.mx);
      this.ty = this.pan.ty + (ev.clientY - r.top - this.pan.my); this.draw(); return; }
    const { n } = this.at(ev);
    if (n !== this.hover) { this.hover = n;
      this.cvRef.nativeElement.style.cursor = n ? 'pointer' : 'grab'; this.draw(); }
  }
  @HostListener('window:mouseup') onUp() {
    if (this.drag && !this.moved && this.focusBox?.nativeElement.checked
        && this.drag.id !== this.focusId()) this.focusOn(this.drag.id);
    if (!this.drag && !this.moved && this.fs()) this.hidePanel();
    this.drag = null; this.pan = null;
    this.cvRef.nativeElement.classList.remove('drag');
  }
  onDbl(ev: MouseEvent) {
    const { n } = this.at(ev);
    if (n) { if (n.pin) { n.pin = false; this.draw(); } else this.focusOn(n.id); }
  }
  onWheel(ev: WheelEvent) {
    ev.preventDefault();
    const r = this.cvRef.nativeElement.getBoundingClientRect();
    const mx = ev.clientX - r.left, my = ev.clientY - r.top;
    const k = Math.exp(-ev.deltaY * 0.0016), ns = Math.min(4, Math.max(0.15, this.scale * k));
    this.tx = mx - (mx - this.tx) * (ns / this.scale);
    this.ty = my - (my - this.ty) * (ns / this.scale);
    this.scale = ns; this.userMoved = true; this.draw();
  }
  private select(n: any) { this.selected.set(n); this.draw(); }
  jump(id: string) {
    const n = this.N.find(x => x.id === id);
    if (n) { this.select(n);
      this.tx = this.W / 2 - n.x * this.scale; this.ty = this.H / 2 - n.y * this.scale; this.draw(); }
    else this.focusOn(id);
  }
  isFS() {
    const g = this.gwrapRef?.nativeElement;
    return document.fullscreenElement === g || (document as any).webkitFullscreenElement === g;
  }
  toggleFS() {
    const g = this.gwrapRef.nativeElement as any;
    if (this.isFS()) ((document as any).exitFullscreen || (document as any).webkitExitFullscreen).call(document);
    else (g.requestFullscreen || g.webkitRequestFullscreen).call(g);
  }
  private onFsChange = () => {
    this.fs.set(this.isFS());
    if (!this.isFS()) this.selected.set(this.selected());
    setTimeout(() => { this.resize(); this.fit(); }, 80);
  };
}
