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

interface StoredGroup {
  keywords: string;
  location: string;
  count:    number;
  offers:   Offer[];
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

  private readonly api = 'http://localhost';

  // ── Search params ────────────────────────────────────────────
  keywords = '';
  location = '';
  days     = 30;
  source: SourceFilter = 'all';

  // ── Search results ───────────────────────────────────────────
  offers:   Offer[] = [];
  loading  = false;
  searched = false;
  error    = '';

  // ── Stored groups (loaded on init) ───────────────────────────
  storedGroups:      StoredGroup[] = [];
  storedLoading      = false;
  expandedGroupKey   = '';

  // ── Local status overrides ───────────────────────────────────
  private statusMap = new Map<string, Offer['status']>();

  constructor(private readonly http: HttpClient) {}

  ngOnInit(): void {
    this.loadStoredGroups();
  }

  // ── Computed ─────────────────────────────────────────────────
  get pipelineCount(): number { return this.offers.filter(o => o.source === 'pipeline').length; }
  get indeedCount():   number { return this.offers.filter(o => o.source === 'indeed').length;   }
  get savedCount():    number { return this.offers.filter(o => this.getStatus(o) === 'saved').length; }
  get appliedCount():  number { return this.offers.filter(o => this.getStatus(o) === 'applied').length; }

  groupKey(g: StoredGroup): string { return `${g.keywords}||${g.location}`; }

  isExpanded(g: StoredGroup): boolean { return this.expandedGroupKey === this.groupKey(g); }

  toggleGroup(g: StoredGroup): void {
    const key = this.groupKey(g);
    this.expandedGroupKey = this.expandedGroupKey === key ? '' : key;
  }

  getStatus(offer: Offer): Offer['status'] {
    return this.statusMap.get(offer.id) ?? offer.status;
  }

  setStatus(offer: Offer, status: Offer['status']): void {
    const current = this.getStatus(offer);
    this.statusMap.set(offer.id, current === status ? 'new' : status);
  }

  // ── Load stored groups (on init) ─────────────────────────────
  loadStoredGroups(): void {
    this.storedLoading = true;
    this.http.get<StoredGroup[]>(`${this.api}/jobs/stored/grouped`, { withCredentials: true }).subscribe({
      next:  (data) => { this.storedGroups = data; this.storedLoading = false; },
      error: ()     => { this.storedLoading = false; },
    });
  }

  // ── Search (API / cache) ─────────────────────────────────────
  load(): void {
    this.loading  = true;
    this.error    = '';
    this.searched = false;

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
        this.offers   = data;
        this.loading  = false;
        this.searched = true;
        // Refresh stored groups in case new offers were saved
        if (this.keywords.trim()) this.loadStoredGroups();
      },
      error: (err) => {
        this.loading  = false;
        this.error    = err?.error?.detail || `Erreur ${err.status}`;
        this.searched = true;
      },
    });
  }

  // ── Letter generation ────────────────────────────────────────
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
      error: ()  => { this.letterLoading[offer.id] = false; this.letterResult[offer.id] = '⚠ Erreur génération lettre'; },
    });
  }

  closeLetter(offerId: string): void { delete this.letterResult[offerId]; }

  scoreColor(score: number | null | undefined): string {
    if (!score) return '#78716C';
    if (score >= 8) return '#6B8E6B';
    if (score >= 5) return '#D9A05B';
    return '#B87373';
  }
}
