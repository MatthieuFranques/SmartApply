import { Component, OnInit, OnDestroy, OnChanges, SimpleChanges, Output, EventEmitter, Input } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { PipelineService, PipelineParams, PipelineConfig } from '../../services/pipeline.service';

interface StreamEvent {
  type:        string;
  phase?:      string;
  status?:     string;
  company?:    string;
  domaine?:    string;
  city?:       string;
  message?:    string;
  total?:      number;
  prescore?:   number;
  deep_score?: number;
}

interface PhaseStats {
  found:      number;
  kept:       number;
  eliminated: number;
  errors:     number;
}

type ViewState = 'config' | 'running' | 'done';

@Component({
  selector:    'app-pipeline',
  standalone:  true,
  imports:     [CommonModule, FormsModule],
  templateUrl: './pipeline.component.html',
  styleUrls:   ['./pipeline.component.scss'],
})
export class PipelineComponent implements OnInit, OnDestroy {

  @Input()  visible    = false;
  @Output() closed       = new EventEmitter<void>();
  @Output() pipelineDone = new EventEmitter<void>();

  // ── Config data ──────────────────────────────────────────
  config: PipelineConfig | null = null;

  // ── Scraping params ──────────────────────────────────────
  cityInput     = '';
  cities        : string[] = ['Toulouse'];
  customSector  = '';
  allSectors    : string[] = [];
  activeSectors : string[] = [];
  maxResults    = 100;
  keywordMatch  : 'any' | 'all' = 'any';

  // ── Filter params ────────────────────────────────────────
  minPrescore  = 4;
  minDeepScore = 5;
  skipDeep     = false;

  // ── Pipeline state ───────────────────────────────────────
  view: ViewState = 'config';
  currentPhase = '';
  events: StreamEvent[] = [];

  stats: Record<string, PhaseStats> = {
    scraping: { found: 0, kept: 0, eliminated: 0, errors: 0 },
    filter:   { found: 0, kept: 0, eliminated: 0, errors: 0 },
    enrich:   { found: 0, kept: 0, eliminated: 0, errors: 0 },
  };

  phases = [
    { key: 'scraping', label: 'SCRAPING',      icon: '○' },
    { key: 'filter',   label: 'FILTRAGE',       icon: '○' },
    { key: 'enrich',   label: 'ENRICHISSEMENT', icon: '○' },
  ];

  private sub?: Subscription;

  get running(): boolean { return this.view === 'running'; }
  get done():    boolean { return this.view === 'done'; }

  constructor(private readonly pipeline: PipelineService) {}

  ngOnInit(): void {
    this.pipeline.getPipelineConfig().subscribe({
      next: (cfg) => {
        this.config       = cfg;
        this.allSectors   = cfg.scraping.default_sectors;
        this.activeSectors = [...cfg.scraping.default_sectors];
        this.maxResults   = cfg.scraping.max_results.default;
        this.minPrescore  = cfg.filter.min_prescore.default;
        this.minDeepScore = cfg.filter.min_deep_score.default;
        this.skipDeep     = cfg.filter.skip_deep.default;
      },
    });
  }


  ngOnDestroy(): void { this.sub?.unsubscribe(); }


  // ── Modal control ────────────────────────────────────────
  close(): void {
    if (!this.running) this.closed.emit();
  }

  onBackdrop(event: MouseEvent): void {
    if ((event.target as HTMLElement).classList.contains('modal-backdrop')) {
      this.close();
    }
  }

  // ── City management ──────────────────────────────────────
  addCity(): void {
    const city = this.cityInput.trim();
    if (city && !this.cities.includes(city)) this.cities.push(city);
    this.cityInput = '';
  }

  removeCity(city: string): void {
    this.cities = this.cities.filter(c => c !== city);
  }

  // ── Sector management ────────────────────────────────────
  toggleSector(sector: string): void {
    if (this.activeSectors.includes(sector))
      this.activeSectors = this.activeSectors.filter(s => s !== sector);
    else
      this.activeSectors.push(sector);
  }

  addCustomSector(): void {
    const s = this.customSector.trim();
    if (s && !this.allSectors.includes(s)) {
      this.allSectors.push(s);
      this.activeSectors.push(s);
    }
    this.customSector = '';
  }

  selectAllSectors(): void { this.activeSectors = [...this.allSectors]; }
  clearAllSectors():  void { this.activeSectors = []; }

  // ── Pipeline control ─────────────────────────────────────
  get canLaunch(): boolean {
    return this.cities.length > 0 && this.activeSectors.length > 0;
  }

  launch(): void {
    this.view = 'running';
    this.events = [];
    this.currentPhase = '';
    this.stats = {
      scraping: { found: 0, kept: 0, eliminated: 0, errors: 0 },
      filter:   { found: 0, kept: 0, eliminated: 0, errors: 0 },
      enrich:   { found: 0, kept: 0, eliminated: 0, errors: 0 },
    };

    const params: PipelineParams = {
      cities:       this.cities,
      sectors:      this.activeSectors,
      maxResults:   this.maxResults,
      keywordMatch: this.keywordMatch,
      minPrescore:  this.minPrescore,
      minDeepScore: this.minDeepScore,
      skipDeep:     this.skipDeep,
    };

    this.sub = this.pipeline.runFullPipeline(params).subscribe({
      next:     (e) => this.handleEvent(e),
      complete: ()  => { if (this.view === 'running') { this.view = 'done'; this.pipelineDone.emit(); } },
      error:    ()  => { if (this.view === 'running') this.view = 'done'; },
    });
  }

  stop(): void {
    this.sub?.unsubscribe();
    this.view = 'done';
  }

  relancer(): void {
    this.view = 'config';
    this.events = [];
    this.currentPhase = '';
  }

  // ── Event handling ───────────────────────────────────────
  get phaseStatus(): Record<string, 'pending' | 'active' | 'done'> {
    const order = ['scraping', 'filter', 'enrich'];
    const result: Record<string, 'pending' | 'active' | 'done'> = {};
    const currentIndex = order.indexOf(this.currentPhase);

    for (const p of order) {
      const i = order.indexOf(p);
      if (this.done)               result[p] = 'done';
      else if (i < currentIndex)   result[p] = 'done';
      else if (i === currentIndex) result[p] = 'active';
      else                         result[p] = 'pending';
    }
    return result;
  }

  private handleEvent(e: StreamEvent): void {
    if (this.isStateChange(e)) return;
    const phase = e.phase || this.currentPhase;
    if (phase && this.stats[phase]) this.updatePhaseStats(phase, e);
    this.addVisibleEvent(e, phase);
  }

  private isStateChange(e: StreamEvent): boolean {
    if (e.type === 'phase') { this.currentPhase = e.phase!; return true; }
    if (e.type === 'done')  { return true; }
    return false;
  }

  private updatePhaseStats(phase: string, e: StreamEvent): void {
    const s = this.stats[phase];
    if (e.type === 'company') s.found++;
    if (e.type === 'result') {
      if (['kept', 'ok'].includes(e.status!)) s.kept++;
      else if (e.status === 'eliminated') s.eliminated++;
      else if (e.status === 'error') s.errors++;
    }
  }

  private addVisibleEvent(e: StreamEvent, phase: string): void {
    const visible = ['company', 'result', 'done', 'error', 'city', 'pipeline_done'];
    if (visible.includes(e.type)) {
      this.events.unshift({ ...e, phase });
      if (this.events.length > 200) this.events.pop();
    }
  }

  eventLabel(e: StreamEvent): string {
    switch (e.type) {
      case 'company':
        return `${e.company} · ${e.domaine}`;
      case 'result':
        if (e.status === 'kept' || e.status === 'ok')
          return `✓ ${e.company}${e.prescore ? ' · pre:' + e.prescore : ''}${e.deep_score ? ' · ai:' + e.deep_score : ''}`;
        if (e.status === 'eliminated') return `✗ ${e.company}`;
        if (e.status === 'error')      return `⚠ ${e.company} — ${e.message ?? ''}`;
        return e.company ?? '';
      case 'city':          return `→ ${e.city}`;
      case 'done':          return `Phase terminée · ${e.total ?? ''} traités`;
      case 'error':         return `⚠ ${e.message}`;
      case 'pipeline_done': return 'Pipeline terminé';
      default:              return '';
    }
  }

  phaseColor(phase: string): string {
    const colors: Record<string, string> = {
      scraping: '#0066ff',
      filter:   '#ffaa00',
      enrich:   '#00e5a0',
    };
    return colors[phase] ?? '#4a5068';
  }
}
