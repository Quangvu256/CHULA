import { Component, inject } from '@angular/core';
import { AppState } from './state';
import { CheckTab } from './check';
import { RequirementsTab } from './requirements';
import { GraphTab } from './graph';
import { MethodTab } from './method';
import { PoliciesTab } from './policies';

@Component({
  selector: 'app-root',
  imports: [CheckTab, RequirementsTab, GraphTab, MethodTab, PoliciesTab],
  template: `
  <div class="wrap">
    <h1>ISO 19650 &rarr; Predictive Maintenance</h1>
    <p class="sub">Readiness checker for IFC models, and an explorer for the knowledge graph
      they are checked against.</p>
    <div class="tabs">
      <button [class.on]="st.activeTab()===1" (click)="st.activeTab.set(1)">Check IFC</button>
      <button [class.on]="st.activeTab()===2" (click)="st.activeTab.set(2)">Requirements &amp; why</button>
      <button [class.on]="st.activeTab()===3" (click)="st.activeTab.set(3)">Explore graph</button>
      <button [class.on]="st.activeTab()===4" (click)="st.activeTab.set(4)">Method &amp; accuracy</button>
      <button [class.on]="st.activeTab()===5" (click)="st.activeTab.set(5)">Policies &amp; privacy</button>
    </div>
    <section class="tab" [class.on]="st.activeTab()===1"><check-tab/></section>
    <section class="tab" [class.on]="st.activeTab()===2"><requirements-tab/></section>
    <section class="tab" [class.on]="st.activeTab()===3"><graph-tab/></section>
    <section class="tab" [class.on]="st.activeTab()===4"><method-tab/></section>
    <section class="tab" [class.on]="st.activeTab()===5"><policies-tab/></section>
  </div>`,
})
export class App { st = inject(AppState); }
