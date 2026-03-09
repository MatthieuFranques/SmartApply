// dashboard.component.ts

import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Company } from '../../models/company.model';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent {

  city          : string    = 'Toulouse';
  companies     : Company[] = [];
  loading       : boolean   = false;
  statusMessage : string    = '';

  private api = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  // ─── Stats calculées ─────────────────────────────────────

  get recruiting()  { return this.companies.filter(c => c.is_recruiting).length; }
  get withOffers()  { return this.companies.filter(c => c.job_offers?.length).length; }
  get withContact() { return this.companies.filter(c => c.contact_form?.url).length; }

  // ─── Actions pipeline ────────────────────────────────────

  onScrape() {
    this.loading = true;
    this.statusMessage = 'Scraping en cours...';
    this.http.post(`${this.api}/scraping/start`, { cities: [this.city] })
      .subscribe({
        next: () => {
          this.statusMessage = '✅ Scraping terminé';
          this.loadResults();
        },
        error: () => {
          this.statusMessage = '❌ Erreur scraping';
          this.loading = false;
        },
        complete: () => this.loading = false
      });
  }

  onFilter() {
    this.loading = true;
    this.statusMessage = 'Filtrage en cours...';
    this.http.post(`${this.api}/filter/start`, { cities: [this.city] })
      .subscribe({
        next: () => {
          this.statusMessage = '✅ Filtrage terminé';
          this.loadResults();
        },
        error: () => {
          this.statusMessage = '❌ Erreur filtrage';
          this.loading = false;
        },
        complete: () => this.loading = false
      });
  }

  onEnrich() {
    this.loading = true;
    this.statusMessage = 'Enrichissement en cours...';
    this.http.post(`${this.api}/enrich/start-sync`, {
      input_file: `results/${this.city.toLowerCase()}/deep_results-${this.city.toLowerCase()}.json`
    }).subscribe({
      next: () => {
        this.statusMessage = '✅ Enrichissement terminé';
        this.loadResults();
      },
      error: () => {
        this.statusMessage = '❌ Erreur enrichissement';
        this.loading = false;
      },
      complete: () => this.loading = false
    });
  }

  // ─── Chargement des résultats ────────────────────────────

  loadResults() {
    this.http.get<Company[]>(
      `${this.api}/enrich/results/${this.city.toLowerCase()}`
    ).subscribe({
      next: (data) => this.companies = data,
      error: () => this.statusMessage += ' (aucun résultat chargé)'
    });
  }
}