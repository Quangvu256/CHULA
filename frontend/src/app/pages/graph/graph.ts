import { AfterViewInit, Component, ElementRef, HostListener, OnDestroy, ViewChild,
         effect, inject, signal } from '@angular/core';
import { Api } from '../../core/api';
import { AppState } from '../../core/state';

/** Canvas graph explorer. The physics is the deterministic settle engine ported
 *  verbatim from the previous UI: phyllotaxis seed (no Math.random), monotonic
 *  alpha decay rendered over ~90 frames, then a dead stop - so the same filter
 *  always produces the same picture and nothing wobbles at rest. */
const USECASE = ['term_condition_monitoring_system','term_scada_system','term_condition_observation',
 'term_asset_operational_data','term_pdm_model','term_health_indicator','term_anomaly_event',
 'term_remaining_useful_life_prediction','term_maintenance_alert','term_maintenance_work_order',
 'term_maintenance_intervention_outcome','term_failure_mode','term_asset_failure_history',
 'term_maintenance_history','term_asset_criticality','term_asset_condition_duty',
 'term_hs_incident','term_near_miss','term_hs_risk','term_risk_treatment','term_treatment_control',
 'term_level_of_risk','term_likelihood','term_consequence','term_risk_urgency_prioritization',
 'term_hs_register','term_hs_properties','term_foreseen_trigger_event','trigger_maintenance_work',
 'term_security_information_requirements','term_asset','term_aim'];
const PCOL: Record<string, string> = {'ISO 19650-1':'--p1','ISO 19650-2':'--p2','ISO 19650-3':'--p3',
 'ISO 19650-4':'--p4','ISO 19650-5':'--p5','ISO 19650-6':'--p6'};
const SIM = {CH:-1500, LD:95, LS:0.09, GR:0.035, VD:0.62, VMAX:28};

@Component({
  selector: 'graph-tab',
  template: `
  <div class="gbar">
    <strong style="font-size:13px">View:</strong>
    <button class="b" [class.on]="view()==='usecase'" (click)="preset('usecase')">PdM use case</button>
    <button class="b" [class.on]="view()==='high'" (click)="preset('high')">High-PdM only</button>
    <button class="b" [class.on]="view()==='all'" (click)="preset('all')">Everything</button>
  </div>
  <div class="gbar">
    <input type="search" placeholder="Search name or id&hellip;" [value]="q()"
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
        <h3>{{n.name}}</h3>
        <div class="src"><span class="dot" [style.background]="'var('+(pcol[n.part]||'--mut')+')'"></span>
          {{n.part}} &middot; {{n.label}} &middot; PdM {{n.pdm}} &middot; <code>{{n.id}}</code></div>
        <div class="row" style="margin-top:10px">
          <button class="b" (click)="focusOn(n.id)">Show only this neighbourhood</button></div>
        <div class="k">Definition</div><div>{{n.def}}</div>
        <div class="k">Provenance</div><div>{{n.std}} &mdash; clause {{n.cl}}</div>
        @if (n.note) {<div class="k">Note</div><div class="src" style="font-size:12px">{{n.note}}</div>}
        <div class="k">Outgoing ({{outEdges().length}})</div>
        @for (e of outEdges(); track $index) {
          <div class="nb" (click)="jump(e.t)">
            <span class="dot" [style.background]="'var('+(pcol[nodeOf(e.t)?.part]||'--mut')+')'"></span>
            &rarr; <b>{{e.type}}</b> {{nodeOf(e.t)?.name}}
            <div class="src">{{e.std}} {{e.cl}}</div></div>
        } @empty {<div class="src">none</div>}
        <div class="k">Incoming ({{inEdges().length}})</div>
        @for (e of inEdges(); track $index) {
          <div class="nb" (click)="jump(e.s)">
            <span class="dot" [style.background]="'var('+(pcol[nodeOf(e.s)?.part]||'--mut')+')'"></span>
            &larr; <b>{{e.type}}</b> {{nodeOf(e.s)?.name}}
            <div class="src">{{e.std}} {{e.cl}}</div></div>
        } @empty {<div class="src">none</div>}
      } @else if (!fs()) {
        <p class="hint">Click a node to read its definition, its clause, and its neighbours.
        Drag to move a node, scroll to zoom, drag the background to pan.</p>
      }
    </div>
  </div>
  <div class="legend">
    @for (p of partKeys; track p) {
      <span><span class="dot" [style.background]="'var('+pcol[p]+')'"></span>{{p}}</span>
    }
    <span>node size = number of connections</span>
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
  view = signal('usecase');
  q = signal('');
  hidden = signal(new Set<string>());
  focusId = signal<string | null>(null);
  selected = signal<any | null>(null);
  count = signal('');
  fs = signal(false);

  private G: any = null;
  private byId: Record<string, any> = {};
  private N: any[] = [];
  private E: any[] = [];
  private ctx!: CanvasRenderingContext2D;
  private W = 0; private H = 0; private scale = 1; private tx = 0; private ty = 0;
  private simAlpha = 0; private anim = 0;
  private drag: any = null; private pan: any = null; private hover: any = null;
  private moved = false; private userMoved = false;

  constructor() {
    // other tabs can ask us to focus a node
    effect(() => {
      const id = this.st.pendingFocus();
      if (id && this.G) { this.st.pendingFocus.set(null); this.showNode(id); }
    });
  }

  ngAfterViewInit() {
    this.ctx = this.cvRef.nativeElement.getContext('2d')!;
    this.api.graph().then(g => {
      this.G = g;
      g.nodes.forEach((n: any) => this.byId[n.id] = n);
      this.resize(); this.rebuild(true);
      const id = this.st.pendingFocus();
      if (id) { this.st.pendingFocus.set(null); this.showNode(id); }
    });
    document.addEventListener('fullscreenchange', this.onFsChange);
    (document as any).addEventListener('webkitfullscreenchange', this.onFsChange);
  }
  ngOnDestroy() {
    cancelAnimationFrame(this.anim);
    document.removeEventListener('fullscreenchange', this.onFsChange);
    (document as any).removeEventListener('webkitfullscreenchange', this.onFsChange);
  }

  private cssv(v: string) { return getComputedStyle(document.documentElement).getPropertyValue(v).trim(); }
  nodeOf(id: string) { return this.byId[id]; }
  outEdges() { const s = this.selected(); return s ? this.E.filter(e => e.s === s.id) : []; }
  inEdges() { const s = this.selected(); return s ? this.E.filter(e => e.t === s.id) : []; }

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
    let keep: Set<string>;
    if (focusId) {
      keep = new Set([focusId]);
      this.G.edges.forEach((e: any) => { if (e.s === focusId) keep.add(e.t); if (e.t === focusId) keep.add(e.s); });
    } else if (this.view() === 'all') keep = new Set(this.G.nodes.map((n: any) => n.id));
    else if (this.view() === 'high') keep = new Set(this.G.nodes.filter((n: any) => n.pdm === 'high').map((n: any) => n.id));
    else keep = new Set(USECASE.filter(s => this.byId[s]));
    if (q && !focusId) {
      const hit = new Set(this.G.nodes
        .filter((n: any) => n.name.toLowerCase().includes(q) || n.id.includes(q)).map((n: any) => n.id));
      const grow = new Set(hit);
      this.G.edges.forEach((e: any) => { if (hit.has(e.s)) grow.add(e.t); if (hit.has(e.t)) grow.add(e.s); });
      keep = grow as Set<string>;
    }
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
    this.count.set(`${this.N.length} nodes, ${this.E.length} relationships`
      + (focusId ? ` (focused on ${this.byId[focusId].name})` : ''));
    if (relayout) { this.seed(); this.userMoved = false;
      this.selected.set(focusId ? this.N.find(n => n.id === focusId) || null : null);
      this.settle(this.N.length > 200 ? 760 : 440); }
    else { this.fit(); }
  }

  private seed() {
    const A = Math.PI * (3 - Math.sqrt(5));
    this.N.forEach((n, i) => { const r = 16 * Math.sqrt(0.5 + i), a = i * A;
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
  private rad(n: any) { return 4 + Math.min(9, Math.sqrt(n.deg || 1) * 2.1); }
  private draw() {
    const ctx = this.ctx; if (!ctx) return;
    ctx.clearRect(0, 0, this.W, this.H);
    const sel = this.selected();
    const nbr = sel ? new Set(this.E.filter(e => e.s === sel.id || e.t === sel.id)
                                    .flatMap(e => [e.s, e.t])) : null;
    ctx.lineWidth = 1;
    for (const e of this.E) {
      const on = sel && (e.s === sel.id || e.t === sel.id);
      ctx.strokeStyle = on ? this.cssv('--acc') : this.cssv('--edge');
      ctx.globalAlpha = sel ? (on ? 0.95 : 0.13) : 0.5;
      ctx.beginPath();
      ctx.moveTo(e.a.x * this.scale + this.tx, e.a.y * this.scale + this.ty);
      ctx.lineTo(e.b.x * this.scale + this.tx, e.b.y * this.scale + this.ty); ctx.stroke();
    }
    ctx.globalAlpha = 1;
    for (const a of this.N) {
      const X = a.x * this.scale + this.tx, Y = a.y * this.scale + this.ty;
      const r = this.rad(a) * Math.min(1.5, Math.max(0.6, this.scale));
      const dim = sel && nbr && !nbr.has(a.id);
      ctx.globalAlpha = dim ? 0.2 : 1;
      ctx.beginPath(); ctx.arc(X, Y, r, 0, 6.284);
      ctx.fillStyle = this.cssv(PCOL[a.part] || '--mut'); ctx.fill();
      if (a === sel || a === this.hover) {
        ctx.lineWidth = 2.5; ctx.strokeStyle = this.cssv('--fg'); ctx.stroke(); ctx.lineWidth = 1; }
      if (a.pin) { ctx.globalAlpha = dim ? 0.2 : 0.6; ctx.beginPath(); ctx.arc(X, Y, r + 3.5, 0, 6.284);
        ctx.strokeStyle = this.cssv('--mut'); ctx.stroke(); }
      if (!dim && (this.scale > 0.7 || a === sel || a === this.hover || this.N.length < 50)) {
        ctx.globalAlpha = 0.93; ctx.fillStyle = this.cssv('--fg');
        ctx.font = '11px ui-sans-serif,-apple-system,sans-serif'; ctx.textAlign = 'center';
        const t = a.name.length > 30 ? a.name.slice(0, 29) + '...' : a.name;
        ctx.fillText(t, X, Y - r - 4); }
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
    if (!this.isFS()) this.selected.set(this.selected()); // keep selection, panel reverts to sidebar
    setTimeout(() => { this.resize(); this.fit(); }, 80);
  };
}
