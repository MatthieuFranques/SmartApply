// src/app/components/pipeline/pipeline.component.ts
import { Component, OnDestroy, Output, EventEmitter } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';
import { PipelineService } from '../../services/pipeline.service';

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
  summary?:    string;
}

interface PhaseStats {
  found:      number;
  kept:       number;
  eliminated: number;
  errors:     number;
}

@Component({
  selector:    'app-pipeline',
  standalone:  true,
  imports:     [CommonModule, FormsModule],
  templateUrl: './pipeline.component.html',
  styleUrls:   ['./pipeline.component.scss'],
})
export class PipelineComponent implements OnDestroy {

  @Output() pipelineDone = new EventEmitter<void>();

  city    = 'Toulouse';
  running = false;
  done    = false;

  currentPhase = '';
  events: StreamEvent[] = [];

  stats: Record<string, PhaseStats> = {
    scraping: { found: 0, kept: 0, eliminated: 0, errors: 0 },
    filter:   { found: 0, kept: 0, eliminated: 0, errors: 0 },
    enrich:   { found: 0, kept: 0, eliminated: 0, errors: 0 },
  };

  phases = [
    { key: 'scraping', label: 'SCRAPING',      icon: '🔍' },
    { key: 'filter',   label: 'FILTRAGE',       icon: '⚡' },
    { key: 'enrich',   label: 'ENRICHISSEMENT', icon: '🧬' },
  ];

  private sub?: Subscription;

  constructor(private readonly pipeline: PipelineService) {}

  ngOnDestroy(): void { this.sub?.unsubscribe(); }

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

  launch(): void {
    this.running      = true;
    this.done         = false;
    this.events       = [];
    this.currentPhase = '';
    this.stats = {
      scraping: { found: 0, kept: 0, eliminated: 0, errors: 0 },
      filter:   { found: 0, kept: 0, eliminated: 0, errors: 0 },
      enrich:   { found: 0, kept: 0, eliminated: 0, errors: 0 },
    };

    this.sub = this.pipeline.runFullPipeline([this.city]).subscribe({
      next:     (e) => this.handleEvent(e),
      complete: ()  => { this.running = false; },
      error:    ()  => { this.running = false; },
    });
  }

  stop(): void {
    this.sub?.unsubscribe();
    this.running = false;
  }

private handleEvent(e: StreamEvent): void {
    // 1. Gestion des changements d'état globaux (Phase / Fin)
    if (this.isStateChange(e)) return;

    const phase = e.phase || this.currentPhase;

    // 2. Mise à jour des compteurs (Stats)
    if (phase && this.stats[phase]) {
      this.updatePhaseStats(phase, e);
    }

    // 3. Gestion de la liste des événements visuels
    this.addVisibleEvent(e, phase);
  }

  private isStateChange(e: StreamEvent): boolean {
    if (e.type === 'phase') {
      this.currentPhase = e.phase!;
      return true;
    }
    if (e.type === 'pipeline_done') {
      this.done = true;
      this.running = false;
      this.events.unshift(e);
      this.pipelineDone.emit();
      return true;
    }
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
    const visibleTypes = ['company', 'result', 'done', 'error', 'city', 'pipeline_done'];
    if (visibleTypes.includes(e.type)) {
      this.events.unshift({ ...e, phase });
      if (this.events.length > 200) {
        this.events.pop();
      }
    }
  }

  eventLabel(e: StreamEvent): string {
    switch (e.type) {
      case 'company':
        return `${e.company} (${e.domaine})`;
      case 'result':
        if (e.status === 'kept' || e.status === 'ok')
          return `✅ ${e.company}${e.prescore ? ' · pre:' + e.prescore : ''}${e.deep_score ? ' · deep:' + e.deep_score : ''}`;
        if (e.status === 'eliminated') return `✗ ${e.company}`;
        if (e.status === 'error')      return `⚠ ${e.company} — ${e.message || ''}`;
        return e.company || '';
      case 'city':         return `📍 ${e.city}`;
      case 'done':         return `Phase terminée — ${e.total ?? ''} traités`;
      case 'error':        return `❌ ${e.message}`;
      case 'pipeline_done': return '🎉 Pipeline terminé !';
      default:             return '';
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