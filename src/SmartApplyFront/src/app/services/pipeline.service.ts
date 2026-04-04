// app/services/pipeline.service.ts
import { Injectable } from '@angular/core';
import { concat, Observable } from 'rxjs';

@Injectable({ providedIn: 'root' })
export class PipelineService {

  private api = 'http://localhost:8000';


  runFullPipeline(cities: string[]): Observable<any> {
    // On enchaîne les 3 streams l'un après l'autre
    return concat(
      this.streamScraping(cities),
      this.streamFilter(),
      this.streamEnrich()
    ).pipe(
      // Optionnel : on peut ajouter un message final pour déclencher 'pipeline_done' côté front
      // ou laisser le backend envoyer l'événement via le dernier stream.
    );
  }

  streamScraping(cities: string[]): Observable<any> {
    return this._sse(`${this.api}/scraping/stream?cities=${cities.join(',')}`);
  }

  streamFilter(): Observable<any> {
    return this._sse(`${this.api}/filter/stream`);
  }

  streamEnrich(): Observable<any> {
    return this._sse(`${this.api}/enrich/stream`);
  }

  private _sse(url: string): Observable<any> {
    return new Observable(observer => {
      const es = new EventSource(url, { withCredentials: true });

      es.onmessage = (event) => {
        try {
          observer.next(JSON.parse(event.data));
        } catch {}
      };

      es.onerror = (err) => {
        es.close();
        observer.complete();
      };

      // Cleanup à l'unsubscribe
      return () => es.close();
    });
  }
}