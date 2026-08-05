import { Component, inject } from '@angular/core';
import { AppState } from './core/state';
import { CheckTab } from './pages/check/check';
import { RequirementsTab } from './pages/requirements/requirements';
import { GraphTab } from './pages/graph/graph';
import { MethodTab } from './pages/method/method';
import { PoliciesTab } from './pages/policies/policies';
import { FusekiTab } from './pages/fuseki/fuseki';

@Component({
  selector: 'app-root',
  imports: [CheckTab, RequirementsTab, GraphTab, MethodTab, PoliciesTab, FusekiTab],
  template: `
  <div class="wrap">
    <h1>ISO 19650 &rarr; Predictive Maintenance (RDF + SHACL)</h1>
    <p class="sub">Readiness checker for IFC models, W3C SPARQL Explorer, and Apache Jena Fuseki Monitoring dashboard.</p>
    <div class="tabs">
      <button [class.on]="st.activeTab()===1" (click)="st.activeTab.set(1)">Check IFC</button>
      <button [class.on]="st.activeTab()===2" (click)="st.activeTab.set(2)">Requirements &amp; why</button>
      <button [class.on]="st.activeTab()===3" (click)="st.activeTab.set(3)">Explore graph</button>
      <button [class.on]="st.activeTab()===6" (click)="st.activeTab.set(6)">Fuseki Monitoring</button>
      <button [class.on]="st.activeTab()===4" (click)="st.activeTab.set(4)">Method &amp; accuracy</button>
      <button [class.on]="st.activeTab()===5" (click)="st.activeTab.set(5)">Policies &amp; privacy</button>
    </div>
    <section class="tab" [class.on]="st.activeTab()===1"><check-tab/></section>
    <section class="tab" [class.on]="st.activeTab()===2"><requirements-tab/></section>
    <section class="tab" [class.on]="st.activeTab()===3"><graph-tab/></section>
    <section class="tab" [class.on]="st.activeTab()===6"><fuseki-tab/></section>
    <section class="tab" [class.on]="st.activeTab()===4"><method-tab/></section>
    <section class="tab" [class.on]="st.activeTab()===5"><policies-tab/></section>
  </div>`,
})
export class App { st = inject(AppState); }
