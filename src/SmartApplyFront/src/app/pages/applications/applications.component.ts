import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

export interface Candidature {
  id:          string;
  entreprise:  string;
  poste:       string;
  statut:      string;
  ville:       string;
  date:        string;
  expediteur:  string;
  gmail_link:  string;
}

export interface SyncResult {
  total_analyses:  number;
  nouvelles:       number;
  mises_a_jour:    number;
  ignorees:        number;
  sans_poste:      number;
  derniere_sync:   string;
}

export interface SyncStatus {
  derniere_sync:       string | null;
  total_en_cache:      number;
  jamais_synchronise:  boolean;
}

@Component({
  selector: 'app-applications',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './applications.component.html',
  styleUrls: ['./applications.component.scss']
})
export class ApplicationsComponent implements OnInit {

  // ── Auth ───────────────────────────────────────────────
  authenticated = false;
  authChecking  = true;

  // ── Données ────────────────────────────────────────────
  candidatures: Candidature[] = [];
  loading       = false;
  syncing       = false;   // true pendant un appel Gmail (sync)
  error         = '';

  // ── Sync info ──────────────────────────────────────────
  syncStatus:   SyncStatus | null = null;
  lastSyncResult: SyncResult | null = null;

  // ── Filtres ────────────────────────────────────────────
  statuts      = ['Tous', 'En attente', 'Entretien', 'Offre reçue', 'Décision requise', 'Refusé'];
  activeStatut = 'Tous';

  private api = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.checkAuth();
  }

  // ── Auth ───────────────────────────────────────────────

  checkAuth(): void {
    this.authChecking = true;
    this.http.get<{ authenticated: boolean }>(`${this.api}/gmail/status`).subscribe({
      next: (res) => {
        this.authenticated = res.authenticated;
        this.authChecking  = false;
        if (this.authenticated) this.init();
      },
      error: () => {
        this.authenticated = false;
        this.authChecking  = false;
      }
    });
  }

  connectGmail(): void {
    window.location.href = `${this.api}/gmail/auth`;
  }

  // ── Init : charge le cache puis vérifie si sync nécessaire ─

  init(): void {
    this.loadFromCache();
    this.loadSyncStatus();
  }

  loadSyncStatus(): void {
    this.http.get<SyncStatus>(`${this.api}/candidatures/status`).subscribe({
      next: (status) => {
        this.syncStatus = status;
        // Première utilisation : sync automatique
        if (status.jamais_synchronise) {
          this.syncGmail(false);
        }
      },
      error: () => {}
    });
  }

  // ── Lecture cache local (sans appel Gmail) ─────────────

  loadFromCache(): void {
    this.loading = true;
    this.error   = '';
    this.http.get<Candidature[]>(`${this.api}/candidatures`).subscribe({
      next:  (data) => { this.candidatures = data; this.loading = false; },
      error: ()     => { this.loading = false; }
    });
  }

  // ── Sync Gmail (appel API Google) ──────────────────────

  syncGmail(forceFull: boolean = false): void {
    this.syncing = true;
    this.error   = '';
    this.lastSyncResult = null;

    this.http.post<SyncResult>(
      `${this.api}/candidatures/sync?force_full=${forceFull}`, {}
    ).subscribe({
      next: (result) => {
        this.lastSyncResult = result;
        this.syncing        = false;
        this.loadFromCache();   // recharge depuis le JSON mis à jour
        this.loadSyncStatus();
      },
      error: (err) => {
        this.syncing = false;
        if (err.status === 401) {
          this.authenticated = false;
          this.error = 'Session expirée. Reconnecte-toi.';
        } else {
          this.error = 'Erreur lors de la synchronisation Gmail.';
        }
      }
    });
  }

  // ── Rafraîchir = sync depuis la dernière date ──────────
  onRefresh(): void {
    this.syncGmail(false);
  }

  // ── Tout resync (reset) ────────────────────────────────
  onFullReset(): void {
    if (!confirm('Réinitialiser tout l\'historique et tout resynchroniser ?')) return;
    this.http.delete(`${this.api}/candidatures/reset`).subscribe({
      next: () => this.syncGmail(true),
      error: () => { this.error = 'Erreur lors de la réinitialisation.'; }
    });
  }

  onFilterChange(statut: string): void {
    this.activeStatut = statut;
  }

  // ── Données filtrées ───────────────────────────────────
  get filtered(): Candidature[] {
    if (this.activeStatut === 'Tous') return this.candidatures;
    return this.candidatures.filter(c => c.statut === this.activeStatut);
  }

  // ── Helpers ────────────────────────────────────────────
  statutClass(statut: string): string {
    const map: Record<string, string> = {
      'En attente':       'attente',
      'Entretien':        'entretien',
      'Offre reçue':      'offre',
      'Décision requise': 'decision',
      'Refusé':           'refuse',
    };
    return map[statut] ?? 'attente';
  }

  senderName(expediteur: string): string {
    const m = expediteur?.match(/^([^<]+)/);
    return m ? m[1].trim() : expediteur;
  }

  initial(entreprise: string): string {
    return entreprise?.charAt(0)?.toUpperCase() ?? '?';
  }

  formatDate(iso: string): string {
    if (!iso) return '—';
    try {
      return new Date(iso).toLocaleDateString('fr-FR');
    } catch {
      return iso;
    }
  }

  formatLastSync(): string {
    const d = this.syncStatus?.derniere_sync;
    if (!d) return 'Jamais synchronisé';
    try {
      return new Date(d).toLocaleString('fr-FR');
    } catch { return d; }
  }

  countByStatut(statut: string): number {
  return this.candidatures.filter(c => c.statut === statut).length;
}
}