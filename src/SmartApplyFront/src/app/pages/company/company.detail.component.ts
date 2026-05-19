import { Component, Input, Output, EventEmitter, OnChanges, HostListener } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

@Component({
  selector: 'app-company-detail',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './company.detail.component.html',
  styleUrls: ['./company.detail.component.scss']
})
export class CompanyDetailComponent implements OnChanges {
  @Input()  company : any = null;
  @Output() closed         = new EventEmitter<void>();
  @Output() deleted        = new EventEmitter<string>();

  private readonly api = 'http://localhost:8000';

  visible           = false;

  // Delete
  showDeleteConfirm = false;
  deleteLoading     = false;

  // Letter
  showLetterEditor  = false;
  letterLoading     = false;
  letterContent     = '';
  letterError       = '';
  copied            = false;

  // Draft
  draftLoading = false;
  draftUrl     = '';
  draftError   = '';

  constructor(private readonly http: HttpClient) {}

  ngOnChanges() {
    this.visible = !!this.company;
    this.showDeleteConfirm = false;
    this.showLetterEditor  = false;
    this.letterContent     = '';
    this.letterError       = '';
    this.copied            = false;
    this.draftLoading      = false;
    this.draftUrl          = '';
    this.draftError        = '';
  }

  @HostListener('document:keydown.escape', ['$event'])
  handleEscape(event: KeyboardEvent) {
    if (this.visible) {
      this.close();
    }
  }
  close() {
    this.visible = false;
    setTimeout(() => this.closed.emit(), 300);
  }

  // ─── Delete ──────────────────────────────────────────────

  confirmDelete() {
    this.showDeleteConfirm = true;
  }

  deleteCompany() {
    this.deleteLoading     = true;
    this.showDeleteConfirm = false;
    const name = encodeURIComponent(this.company.nom);

    this.http.delete(`${this.api}/enrich/delete/${name}`).subscribe({
      next: () => {
        this.deleteLoading = false;
        this.deleted.emit(this.company.nom);
        this.close();
      },
      error: (err) => {
        this.deleteLoading = false;
        console.error('Erreur suppression', err);
      }
    });
  }

  // ─── Cover Letter ─────────────────────────────────────────

  generateLetter() {
    this.letterLoading    = true;
    this.letterError      = '';
    this.showLetterEditor = true;
    this.letterContent    = '';
    const name = encodeURIComponent(this.company.nom);

    this.http.get<{ letter: string | null; contact_form?: Record<string, unknown>; mode: string }>(
      `${this.api}/letter/${name}`,
      { withCredentials: true },
    ).subscribe({
      next: (res) => {
        this.letterLoading = false;
        if (res.letter) {
          this.letterContent = res.letter;
        } else if (res.contact_form) {
          const cf = res.contact_form as Record<string, unknown>;
          if (cf['raw_response']) {
            this.letterContent = cf['raw_response'] as string;
          } else {
            this.letterContent = Object.entries(cf)
              .map(([k, v]) => `${k} : ${v}`)
              .join('\n\n');
          }
        }
      },
      error: (err) => {
        this.letterLoading = false;
        this.letterError   = 'Impossible de générer la lettre. Vérifie que le service est démarré.';
        console.error('Erreur lettre', err);
      }
    });
  }

  copyLetter() {
    navigator.clipboard.writeText(this.letterContent).then(() => {
      this.copied = true;
      setTimeout(() => this.copied = false, 2000);
    });
  }

  // ─── Gmail Draft ──────────────────────────────────────────

  createDraft() {
    this.draftLoading = true;
    this.draftUrl     = '';
    this.draftError   = '';

    this.http.post<{ draft_id: string; draft_url: string; to: string; subject: string }>(
      `${this.api}/gmail/draft`,
      { domaine: this.company.domaine, model: 'mistral' },
      { withCredentials: true },
    ).subscribe({
      next: (res) => {
        this.draftLoading = false;
        this.draftUrl     = res.draft_url;
      },
      error: (err) => {
        this.draftLoading = false;
        this.draftError   = err.status === 403
          ? 'Re-connecte-toi pour activer la création de brouillons Gmail.'
          : 'Erreur lors de la création du brouillon.';
      },
    });
  }

  // ─── Helpers ──────────────────────────────────────────────

  get jobOffers(): any[] {
    return this.company?.job_offers || [];
  }

  get hasContact(): boolean {
    return !!this.company?.contact_form?.url;
  }
}