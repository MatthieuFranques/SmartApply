import { Injectable } from '@angular/core';
import { concat, Observable } from 'rxjs';

export interface PipelineParams {
  cities:       string[];
  sectors:      string[];
  maxResults:   number;
  keywordMatch: 'any' | 'all';
  minPrescore:  number;
  minDeepScore: number;
  skipDeep:     boolean;
}

export interface PipelineConfig {
  scraping: {
    supported_cities: string[];
    default_sectors:  string[];
    max_results:      { default: number; min: number; max: number; step: number };
    keyword_match:    { default: string; options: string[] };
  };
  filter: {
    min_prescore:   { default: number; min: number; max: number };
    min_deep_score: { default: number; min: number; max: number };
    skip_deep:      { default: boolean };
  };
}

@Injectable({ providedIn: 'root' })
export class PipelineService {
  private readonly api = 'http://localhost:8000';

  runFullPipeline(params: PipelineParams): Observable<any> {
    return concat(
      this.streamScraping(params),
      this.streamFilter(params),
      this.streamEnrich(),
    );
  }

  streamScraping(params: PipelineParams): Observable<any> {
    const p = new URLSearchParams({
      cities:        params.cities.join(','),
      sectors:       params.sectors.join(','),
      max_results:   params.maxResults.toString(),
      keyword_match: params.keywordMatch,
    });
    return this._sse(`${this.api}/scraping/stream?${p}`);
  }

  streamFilter(params: PipelineParams): Observable<any> {
    const p = new URLSearchParams({
      min_prescore:   params.minPrescore.toString(),
      min_deep_score: params.minDeepScore.toString(),
      skip_deep:      params.skipDeep.toString(),
    });
    return this._sse(`${this.api}/filter/stream?${p}`);
  }

  streamEnrich(): Observable<any> {
    return this._sse(`${this.api}/enrich/stream`);
  }

  getPipelineConfig(): Observable<PipelineConfig> {
    return new Observable(observer => {
      fetch(`${this.api}/pipeline/config`, { credentials: 'include' })
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
          if (data.type === 'done' || data.type === 'error') {
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
