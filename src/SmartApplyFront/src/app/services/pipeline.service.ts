import { Injectable } from '@angular/core';
import { concat, Observable } from 'rxjs';
import { tap } from 'rxjs/operators';

export interface ScrapingParams {
  cities:        string[];
  sectors:       string[];
  maxResults:    number;
  keywordMatch:  'any' | 'all';
}

@Injectable({ providedIn: 'root' })
export class PipelineService {
  private readonly api = 'http://localhost:8000';

  runFullPipeline(params: ScrapingParams): Observable<any> {
    return concat(
      this.streamScraping(params).pipe(tap(res => console.log('Scraping event:', res))),
      this.streamFilter().pipe(tap(res => console.log('Filter event:', res))),
      this.streamEnrich().pipe(tap(res => console.log('Enrich event:', res))),
    );
  }

  streamScraping(params: ScrapingParams): Observable<any> {
    const p = new URLSearchParams({
      cities:        params.cities.join(','),
      sectors:       params.sectors.join(','),
      max_results:   params.maxResults.toString(),
      keyword_match: params.keywordMatch,
    });
    return this._sse(`${this.api}/scraping/stream?${p}`);
  }

  streamFilter(): Observable<any> {
    return this._sse(`${this.api}/filter/stream`);
  }

  streamEnrich(): Observable<any> {
    return this._sse(`${this.api}/enrich/stream`);
  }

  getScrapingConfig(): Observable<{ default_sectors: string[]; supported_cities: string[] }> {
    return new Observable(observer => {
      fetch(`${this.api}/scraping/config`, { credentials: 'include' })
        .then(r => r.json())
        .then(data => { observer.next(data); observer.complete(); })
        .catch(err => observer.error(err));
    });
  }

  private _sse(url: string): Observable<any> {
    return new Observable(observer => {
      const es = new EventSource(url, { withCredentials: true });

      es.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);
          observer.next(data);
          if (data.type === 'done') {
            es.close();
            observer.complete();
          }
        } catch {
          // ignore parse errors
        }
      };

      es.onerror = () => {
        es.close();
        observer.complete();
      };

      return () => es.close();
    });
  }
}