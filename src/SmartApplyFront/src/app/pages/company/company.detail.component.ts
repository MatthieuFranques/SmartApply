import { Component, Input, Output, EventEmitter, OnChanges } from '@angular/core';
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

  private api = 'http://localhost:8000';

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

  constructor(private http: HttpClient) {}

  ngOnChanges() {
    this.visible = !!this.company;
    // Reset state when company changes
    this.showDeleteConfirm = false;
    this.showLetterEditor  = false;
    this.letterContent     = '';
    this.letterError       = '';
    this.copied            = false;
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

    this.http.get<{ letter: string }>(`${this.api}/letter/${name}`).subscribe({
      next: (res) => {
        this.letterLoading = false;
        this.letterContent = res.letter ?? JSON.stringify(res, null, 2);
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

  // ─── Helpers ──────────────────────────────────────────────

  get jobOffers(): any[] {
    return this.company?.job_offers || [];
  }

  get hasContact(): boolean {
    return !!this.company?.contact_form?.url;
  }
}