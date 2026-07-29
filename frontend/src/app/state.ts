import { Injectable, signal } from '@angular/core';

/** Cross-tab state: the last audit result (Requirements shows PASS/FAIL badges)
 *  and a pending "show this node in the graph" request from other tabs. */
@Injectable({ providedIn: 'root' })
export class AppState {
  lastCheck = signal<any | null>(null);
  activeTab = signal(1);
  pendingFocus = signal<string | null>(null);
  gotoNode(id: string) { this.pendingFocus.set(id); this.activeTab.set(3); }
}
