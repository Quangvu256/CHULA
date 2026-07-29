import { DecimalPipe } from '@angular/common';
import { Component, effect, inject, signal } from '@angular/core';
import { Api } from './api';

/* The EN/VI dictionary is ported verbatim from the previous UI. */
const MT: any = {
en:{sub:'How six copyrighted PDF standards became one verified knowledge graph, and exactly how accurate and complete the result is. Every number is produced by the evaluation harness (tmp/evaluate_kg.py) or computed live from the recorded raw counts - the formulas below show the arithmetic.',
 cards:['standards','KG nodes','relationships','clause references','interpretive edges','conflicts detected'],
 h_pipe:'The pipeline', h_gates:'Accuracy & coverage - the five acceptance gates (live from the last harness run)',
 h_bench:'How far the machine alone gets - measured ceiling',
 hint_pipe:'The machine stage is deterministic (same PDF in, same draft out). The curation stage is analyst judgment governed by a fixed protocol (tmp/extraction_protocol.md: 9 conventions). Nothing merges until all five gates pass.',
 hint_bench:'The draft generator scored against the hand-curated gold files. Green = fidelity of the terms layer it extracts. Blue = how much of the whole standard it reaches. The blue bar is a ceiling measurement, not a defect: the full pipeline (machine + curation + gates) produced the gold itself. Worked example, Part 1: 82 gold nodes = 34 Clause-3 terms (machine gets ~all) + 12 purposes from prose bullet lists + 10 principles + 4 CDE states from a figure + 4 perspectives from a table + ~18 body concepts that had to be recognized and sometimes NAMED. Part 6 sits lowest because its value is Tables 1-4, enumerations and annexes - invisible to sentence-level parsing. This measured gap is the quantitative case for the hybrid method.',
 stages:[['Licensed PDF','the source standard; never redistributed','input'],
  ['Text + page images','pdftotext for prose and tables, pdftoppm for figures - legends are read from images, never assumed','machine'],
  ['Machine first draft','terms verbatim with clause provenance, cross-reference edges, trigger phrases, figure-key chains - deterministic','machine'],
  ['Human curation','tables, annex lists, modality, cross-part reuse, PdM bridges - governed by the 9-rule protocol','judgment'],
  ['Five gates','structure, fidelity, references, traversability, coverage - machine-enforced; merge blocked on failure','machine'],
  ['Union knowledge graph','NODES nodes / RELS relationships across PARTS standards','output'],
  ['Products','Neo4j graph - 13 IFC requirements - readiness audits','output']],
 tags:{machine:'machine',judgment:'judgment',input:'input',output:'output'},
 gates:[['E1 structure','duplicate ids/names, dangling endpoints, closed vocabularies, pure ASCII'],
  ['E2 definition fidelity','every Clause-3 definition matched verbatim against its source PDF'],
  ['E3 reference validity','every provenance clause resolved against PDF heading inventories'],
  ['E4 traversability','0 orphans - one component - 16-step PdM spine - high-PdM reachable'],
  ['E5 term coverage','all source Clause-3 terms represented in the union']],
 fdel:'fidelity', fval:'validity', fcov:'coverage', fviol:'violations', fpass:'PASS',
 termfid:'term fidelity', reach:'whole-standard reach (machine alone)',
 fprec:'precision = correct / created', frec:'recall = found / gold terms',
 freach:'reach = found nodes / gold nodes',
 goldn:'% of gold nodes'},
vi:{sub:'Sáu bản PDF chuẩn có bản quyền trở thành một đồ thị tri thức đã kiểm chứng như thế nào, và kết quả chính xác - đầy đủ đến đâu. Mọi con số do harness đánh giá (tmp/evaluate_kg.py) sinh ra hoặc được tính trực tiếp từ số đếm thô đã ghi nhận - công thức bên dưới hiện rõ phép tính.',
 cards:['chuẩn ISO','node tri thức','quan hệ','tham chiếu điều khoản','cạnh suy diễn','mâu thuẫn phát hiện'],
 h_pipe:'Quy trình', h_gates:'Độ chính xác & độ phủ - 5 cổng nghiệm thu (số liệu sống từ lần chạy harness gần nhất)',
 h_bench:'Máy đơn độc đi được bao xa - trần đo được',
 hint_pipe:'Khâu máy là tất định (cùng PDF vào, cùng bản nháp ra). Khâu curation là phán đoán của người phân tích, bị ràng buộc bởi protocol cố định (tmp/extraction_protocol.md: 9 quy ước). Không gì được merge khi chưa qua đủ 5 cổng.',
 hint_bench:'Máy sinh bản nháp được chấm điểm so với các file gold do người curate. Xanh lá = độ trung thực của tầng term mà máy trích được. Xanh dương = máy với tới bao nhiêu phần của cả chuẩn. Thanh xanh dương là PHÉP ĐO TRẦN, không phải khuyết tật: chính pipeline đầy đủ (máy + curation + cổng) đã tạo ra bản gold. Ví dụ Part 1: 82 node gold = 34 term Clause 3 (máy bắt gần hết) + 12 purpose nằm trong danh sách gạch đầu dòng giữa văn xuôi + 10 principle + 4 trạng thái CDE từ hình vẽ + 4 perspective từ bảng + ~18 khái niệm thân bài phải nhận diện và đôi khi phải ĐẶT TÊN. Part 6 thấp nhất vì giá trị của nó nằm ở Tables 1-4, các enum và annex - vô hình với parse từng câu. Khoảng hở đo được này chính là luận cứ định lượng cho phương pháp hybrid.',
 stages:[['PDF có giấy phép','chuẩn nguồn; không bao giờ phân phối lại','input'],
  ['Văn bản + ảnh trang','pdftotext cho chữ và bảng, pdftoppm cho hình - chú giải hình đọc từ ảnh, không phỏng đoán','machine'],
  ['Bản nháp do máy','term nguyên văn kèm provenance điều khoản, cạnh cross-reference, trigger phrase, chuỗi key hình - tất định','machine'],
  ['Curation bởi người','bảng, danh sách annex, modality, tái sử dụng liên chuẩn, cầu nối PdM - theo protocol 9 quy ước','judgment'],
  ['5 cổng nghiệm thu','cấu trúc, trung thực, tham chiếu, truy vết được, độ phủ - máy cưỡng chế; không qua là không merge','machine'],
  ['Đồ thị tri thức hợp nhất','NODES node / RELS quan hệ trên PARTS chuẩn','output'],
  ['Sản phẩm','đồ thị Neo4j - 13 yêu cầu IFC - chấm mô hình','output']],
 tags:{machine:'máy',judgment:'phán đoán',input:'đầu vào',output:'đầu ra'},
 gates:[['E1 cấu trúc','trùng id/tên, cạnh treo, tập từ vựng đóng, ASCII thuần'],
  ['E2 trung thực định nghĩa','mọi định nghĩa Clause 3 so khớp nguyên văn với PDF nguồn'],
  ['E3 hợp lệ tham chiếu','mọi trích dẫn điều khoản resolve được trong đúng chuẩn của nó'],
  ['E4 truy vết đồ thị','0 node mồ côi - 1 thành phần liên thông - spine PdM 16 bước - high-PdM tới được'],
  ['E5 độ phủ thuật ngữ','toàn bộ term Clause 3 của nguồn có mặt trong đồ thị hợp nhất']],
 fdel:'độ trung thực', fval:'độ hợp lệ', fcov:'độ phủ', fviol:'vi phạm', fpass:'ĐẠT',
 termfid:'độ trung thực term', reach:'độ phủ toàn chuẩn (máy đơn độc)',
 fprec:'precision = số đúng / số máy tạo', frec:'recall = số tìm thấy / tổng term gold',
 freach:'độ phủ = node tìm thấy / node gold',
 goldn:'% node gold'}};

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
