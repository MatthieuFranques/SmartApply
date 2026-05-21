import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

import { StatsBarComponent, StatItem } from '../../components/statsBar/stats-bar.component';

export interface Candidature {
  id: string;
  entreprise: string;
  poste: string;
  statut: string;
  ville: string;
  date: string;
  expediteur: string;
  gmail_link: string;
}

export interface SyncResult {
  total_analyses: number;
  nouvelles: number;
  mises_a_jour: number;
  derniere_sync: string;
}

export interface SyncStatus {
  derniere_sync: string | null;
  total_en_cache: number;
  jamais_synchronise: boolean;
}

@Component({
  selector: 'app-applications',
  standalone: true,
  imports: [CommonModule, StatsBarComponent],
  templateUrl: './applications.component.html',
  styleUrls: ['./applications.component.scss'],
})
export class ApplicationsComponent implements OnInit {

  candidatures   : Candidature[] = [];
  loading        = false;
  syncing        = false;
  error          = '';
  syncStatus     : SyncStatus | null = null;
  lastSyncResult : SyncResult | null = null;

  statuts    = ['Tous', 'En attente', 'Entretien', 'Offre reçue', 'Décision requise', 'Refusé'];
  activeStatut = 'Tous';

  private readonly api = 'http://localhost';

  constructor(private readonly http: HttpClient) {}

  ngOnInit(): void { this.init(); }

  init(): void {
    this.loadFromCache();
    this.loadSyncStatus();
  }

  loadFromCache(): void {
    this.loading = true;
    this.http.get<Candidature[]>(`${this.api}/candidatures`, { withCredentials: true }).subscribe({
      next:  (data) => { this.candidatures = data; this.loading = false; },
      error: ()     => { this.loading = false; this.error = 'Impossible de charger les candidatures.'; },
    });
  }

  loadSyncStatus(): void {
    this.http.get<SyncStatus>(`${this.api}/candidatures/status`, { withCredentials: true }).subscribe({
      next: (status) => {
        this.syncStatus = status;
        if (status.jamais_synchronise) this.syncGmail(false);
      },
    });
  }

  syncGmail(forceFull = false): void {
    this.syncing = true;
    this.error   = '';
    this.http.post<SyncResult>(
      `${this.api}/candidatures/sync?force_full=${forceFull}`, {}, { withCredentials: true }
    ).subscribe({
      next: (result) => {
        this.lastSyncResult = result;
        this.syncing = false;
        this.loadFromCache();
        this.loadSyncStatus();
      },
      error: (err) => {
        this.syncing = false;
        this.error = err.status === 401 ? 'Session Gmail expirée.' : 'Erreur de synchro.';
      },
    });
  }

  onRefresh():   void { this.syncGmail(false); }

  onFullReset(): void {
    if (!confirm('Réinitialiser tout l\'historique ?')) return;
    this.http.delete(`${this.api}/candidatures/reset`, { withCredentials: true }).subscribe({
      next:  () => this.syncGmail(true),
      error: () => this.error = 'Erreur reset.',
    });
  }

  onFilterChange(statut: string): void { this.activeStatut = statut; }

  get filtered(): Candidature[] {
    if (this.activeStatut === 'Tous') return this.candidatures;
    return this.candidatures.filter(c => c.statut === this.activeStatut);
  }

  // ── Stats identiques au dashboard ───────────────────────────
  get statItems(): StatItem[] {
  return [
    { value: this.candidatures.length,         label: 'Total',      color: 'var(--accent)'  },
    { value: this.countByStatut('Entretien'),   label: 'Entretiens', color: 'var(--warning)' },
    { value: this.countByStatut('En attente'),  label: 'En attente', color: '#f97316'        },
    { value: this.countByStatut('Refusé'),      label: 'Refusés',    color: 'var(--danger)'  },
  ];
}

  // ── Helpers ─────────────────────────────────────────────────
  statutClass(s: string): string {
    const map: Record<string, string> = {
      'En attente': 'attente', 'Entretien': 'entretien',
      'Offre reçue': 'offre', 'Décision requise': 'decision', 'Refusé': 'refuse',
    };
    return map[s] ?? 'attente';
  }

  countByStatut(s: string): number { return this.candidatures.filter(c => c.statut === s).length; }
  senderName(e: string):    string { return new RegExp(/^([^<]+)/).exec(e)?.[1].trim() ?? e; }
  initial(ent: string):     string { return ent?.charAt(0)?.toUpperCase() ?? '?'; }
  formatDate(iso: string):  string { return iso ? new Date(iso).toLocaleDateString('fr-FR') : '—'; }

  formatLastSync(): string {
    const d = this.syncStatus?.derniere_sync;
    return d ? new Date(d).toLocaleString('fr-FR') : 'Jamais synchronisé';
  }
}