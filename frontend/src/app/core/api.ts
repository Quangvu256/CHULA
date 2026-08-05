import { Injectable, inject } from '@angular/core';
import { HttpClient, HttpHeaders } from '@angular/common/http';
import { firstValueFrom } from 'rxjs';

/** Thin typed-enough client for the Python backend. Shapes come from the KG
 *  and the generated spec; `any` is deliberate where payloads are large. */
@Injectable({ providedIn: 'root' })
export class Api {
  private http = inject(HttpClient);
  kg()     { return firstValueFrom(this.http.get<any>('/api/kg')); }
  spec()   { return firstValueFrom(this.http.get<any>('/api/spec')); }
  graph()  { return firstValueFrom(this.http.get<any>('/api/graph')); }
  graphRdf() { return firstValueFrom(this.http.get<any>('/api/graph/rdf')); }
  method() { return firstValueFrom(this.http.get<any>('/api/method')); }
  check(file: File) {
    const headers = new HttpHeaders({ 'X-Filename': encodeURIComponent(file.name) });
    return firstValueFrom(this.http.post<any>('/api/check', file, { headers }));
  }
}
