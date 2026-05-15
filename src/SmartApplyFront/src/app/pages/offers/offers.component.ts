import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

export interface Offer {
  id:              string;
  title:           string;
  company:         string;
  location:        string;
  url:             string;
  description?:    string;
  date_posted?:    string;
  source:          'pipeline' | 'indeed';
  status:          'new' | 'saved' | 'applied';
  relevance_score?: number | null;
  tech_required?:  string[];
  domaine?:        string;
  secteur?:        string;
}

type SourceFilter = 'all' | 'pipeline' | 'indeed';

@Component({
  selector:    'app-offers',
  standalone:  true,
  imports:     [CommonModule, FormsModule],
  templateUrl: './offers.component.html',
  styleUrls:   ['./offers.component.scss'],
})
export class OffersComponent implements OnInit {

  private readonly api = 'http://localhost:8000';

  // ── Search params ────────────────────────────────────────
  keywords  = '';
  location  = '';
  days      = 30;
  source    : SourceFilter = 'all';

  // ── State ────────────────────────────────────────────────
  offers    : Offer[] = [];
  loading   = false;
  searched  = false;
  error     = '';

  // ── Local status overrides (no backend needed) ───────────
  private statusMap: Map<string, Offer['status']> = new Map();

  constructor(private readonly http: HttpClient) {}

  ngOnInit(): void { this.load(); }

  // ── Computed ─────────────────────────────────────────────
  get pipelineCount(): number { return this.offers.filter(o => o.source === 'pipeline').length; }
  get indeedCount():   number { return this.offers.filter(o => o.source === 'indeed').length;   }

  get savedCount():   number { return this.offers.filter(o => this.getStatus(o) === 'saved').length; }
  get appliedCount(): number { return this.offers.filter(o => this.getStatus(o) === 'applied').length; }

  getStatus(offer: Offer): Offer['status'] {
    return this.statusMap.get(offer.id) ?? offer.status;
  }

  setStatus(offer: Offer, status: Offer['status']): void {
    const current = this.getStatus(offer);
    this.statusMap.set(offer.id, current === status ? 'new' : status);
  }

  // ── Load ─────────────────────────────────────────────────
  load(): void {
    this.loading = true;
    this.error   = '';

    const params: Record<string, string> = {
      source: this.source,
      days:   this.days.toString(),
      limit:  '150',
    };
    if (this.keywords.trim()) params['keywords'] = this.keywords.trim();
    if (this.location.trim()) params['location']  = this.location.trim();

    const query = new URLSearchParams(params).toString();

    this.http.get<Offer[]>(`${this.api}/jobs/offers?${query}`, { withCredentials: true }).subscribe({
      next: (data) => {
        this.offers  = data;
        this.loading = false;
        this.searched = true;
      },
      error: (err) => {
        this.loading = false;
        this.error   = err?.error?.detail || `Erreur ${err.status}`;
        this.searched = true;
      },
    });
  }

  // ── Letter generation ────────────────────────────────────
  letterLoading: Record<string, boolean> = {};
  letterResult:  Record<string, string>  = {};

  generateLetter(offer: Offer): void {
    if (!offer.domaine) return;
    this.letterLoading[offer.id] = true;
    this.letterResult[offer.id]  = '';

    this.http.get<{ letter: string }>(
      `${this.api}/letter/${encodeURIComponent(offer.company)}`,
      { withCredentials: true },
    ).subscribe({
      next:  (r) => { this.letterLoading[offer.id] = false; this.letterResult[offer.id] = r.letter; },
      error: () => { this.letterLoading[offer.id] = false; this.letterResult[offer.id] = '⚠ Erreur génération lettre'; },
    });
  }

  closeLetter(offerId: string): void { delete this.letterResult[offerId]; }

  scoreColor(score: number | null | undefined): string {
    if (!score) return '#4a5068';
    if (score >= 8) return '#00e5a0';
    if (score >= 5) return '#ffaa00';
    return '#ff4455';
  }
}
