import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

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
  imports: [CommonModule],
  templateUrl: './applications.component.html',
  styleUrls: ['./applications.component.scss']
})
export class ApplicationsComponent implements OnInit {

  // Données
  candidatures: Candidature[] = [];
  loading = false;
  syncing = false; 
  error = '';

  // Sync info
  syncStatus: SyncStatus | null = null;
  lastSyncResult: SyncResult | null = null;

  // Filtres
  statuts = ['Tous', 'En attente', 'Entretien', 'Offre reçue', 'Décision requise', 'Refusé'];
  activeStatut = 'Tous';

  private api = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    // On lance directement l'initialisation (l'auth est gérée par le parent)
    this.init();
  }

  init(): void {
    this.loadFromCache();
    this.loadSyncStatus();
  }

  // Charge les données depuis le cache (MongoDB via FastAPI)
  loadFromCache(): void {
    this.loading = true;
    this.http.get<Candidature[]>(`${this.api}/candidatures`, { withCredentials: true }).subscribe({
      next: (data) => {
        this.candidatures = data;
        this.loading = false;
      },
      error: (err) => {
        this.loading = false;
        this.error = 'Impossible de charger les candidatures.';
      }
    });
  }

  loadSyncStatus(): void {
    this.http.get<SyncStatus>(`${this.api}/candidatures/status`, { withCredentials: true }).subscribe({
      next: (status) => {
        this.syncStatus = status;
        if (status.jamais_synchronise) this.syncGmail(false);
      }
    });
  }

  syncGmail(forceFull: boolean = false): void {
    this.syncing = true;
    this.error = '';
    this.http.post<SyncResult>(`${this.api}/candidatures/sync?force_full=${forceFull}`, {}, { withCredentials: true }).subscribe({
      next: (result) => {
        this.lastSyncResult = result;
        this.syncing = false;
        this.loadFromCache();
        this.loadSyncStatus();
      },
      error: (err) => {
        this.syncing = false;
        this.error = err.status === 401 ? 'Session Gmail expirée.' : 'Erreur de synchro.';
      }
    });
  }

  onRefresh(): void { this.syncGmail(false); }

  onFullReset(): void {
    if (!confirm('Réinitialiser tout l\'historique ?')) return;
    this.http.delete(`${this.api}/candidatures/reset`, { withCredentials: true }).subscribe({
      next: () => this.syncGmail(true),
      error: () => this.error = 'Erreur reset.'
    });
  }

  onFilterChange(statut: string): void { this.activeStatut = statut; }

  get filtered(): Candidature[] {
    if (this.activeStatut === 'Tous') return this.candidatures;
    return this.candidatures.filter(c => c.statut === this.activeStatut);
  }

  // Helpers Template
  statutClass(s: string): string {
    const map: any = { 'En attente': 'attente', 'Entretien': 'entretien', 'Offre reçue': 'offre', 'Décision requise': 'decision', 'Refusé': 'refuse' };
    return map[s] ?? 'attente';
  }

  senderName(e: string): string { return e?.match(/^([^<]+)/)?.[1].trim() ?? e; }
  initial(ent: string): string { return ent?.charAt(0)?.toUpperCase() ?? '?'; }
  formatDate(iso: string): string { return iso ? new Date(iso).toLocaleDateString('fr-FR') : '—'; }
  countByStatut(s: string): number { return this.candidatures.filter(c => c.statut === s).length; }
  
  formatLastSync(): string {
    const d = this.syncStatus?.derniere_sync;
    return d ? new Date(d).toLocaleString('fr-FR') : 'Jamais synchronisé';
  }
}