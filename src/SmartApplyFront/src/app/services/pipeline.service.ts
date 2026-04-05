import { Injectable } from '@angular/core';
import { concat, Observable } from 'rxjs';
import { tap } from 'rxjs/operators'; // Indispensable pour le console.log

@Injectable({ providedIn: 'root' })
export class PipelineService {
  private readonly  api = 'http://localhost:8000';

  runFullPipeline(cities: string[]): Observable<any> {
    // concat attend la complétion de l'Observable précédent pour lancer le suivant
    return concat(
      this.streamScraping(cities).pipe(tap(res => console.log('✅ Scraping event:', res))),
      this.streamFilter().pipe(tap(res => console.log('✅ Filter event:', res))),
      this.streamEnrich().pipe(tap(res => console.log('✅ Enrich event:', res)))
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
          const data = JSON.parse(event.data);
          observer.next(data);

          // TRÈS IMPORTANT : Le signal de fin envoyé par ton FastAPI
          // Si tu ne fermes pas ici, le 'concat' attendra indéfiniment.
          if (data.type === 'done') {
            console.log(`🔚 Fin de flux détectée pour : ${url}`);
            es.close();
            observer.complete();
          }
        } catch (err) {
          console.error("Erreur de parsing JSON sur le flux SSE", err);
        }
      };

      es.onerror = (err) => {
        // En cas d'erreur réseau ou de fermeture par le serveur
        console.log("Flux SSE clos ou terminé.");
        es.close();
        observer.complete();
      };

      // Se déclenche si l'utilisateur annule (unsubscribe)
      return () => es.close();
    });
  }
}