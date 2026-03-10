// dashboard.component.ts

import { Component } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Company } from '../../models/company.model';
import { CompanyDetailComponent } from '../company/company.detail.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, CompanyDetailComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent {

  city            : string   = 'Toulouse';
  companies       : Company[] = [];
  loading         : boolean  = false;
  statusMessage   : string   = '';
  selectedCity    : string   = 'all';
  availableCities : string[] = [];
  selectedCompany : any      = null;

  private api = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  // ─── Stats calculées ─────────────────────────────────────

  get filteredCompanies() {
    if (this.selectedCity === 'all') return this.companies;
    return this.companies.filter(c =>
      c.ville?.toLowerCase() === this.selectedCity.toLowerCase()
    );
  }

  get recruiting()  { return this.filteredCompanies.filter(c => c.is_recruiting).length; }
  get withOffers()  { return this.filteredCompanies.filter(c => c.job_offers?.length).length; }
  get withContact() { return this.filteredCompanies.filter(c => c.contact_form?.url).length; }

  filterByCity(city: string) {
    this.selectedCity = city;
  }

  countByCity(city: string) {
    return this.companies.filter(c =>
      c.ville?.toLowerCase() === city.toLowerCase()
    ).length;
  }

  // ─── Detail panel ────────────────────────────────────────

  openDetail(company: any) {
    this.selectedCompany = company;
  }

  closeDetail() {
    this.selectedCompany = null;
  }

  // ─── Actions pipeline ────────────────────────────────────

  onScrape() {
    this.loading = true;
    this.statusMessage = 'Scraping en cours...';
    this.http.post(`${this.api}/scraping/start`, { cities: [this.city] })
      .subscribe({
        next: () => {
          this.statusMessage = 'Scraping terminé';
          this.loadResults();
        },
        error: () => {
          this.statusMessage = 'Erreur scraping';
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
          this.statusMessage = 'Filtrage terminé';
          this.loadResults();
        },
        error: () => {
          this.statusMessage = 'Erreur filtrage';
          this.loading = false;
        },
        complete: () => this.loading = false
      });
  }

  onEnrich() {
    this.loading = true;
    this.statusMessage = 'Enrichissement en cours...';
    this.http.post(`${this.api}/enrich/start`, {}).subscribe({
      next: () => {
        this.statusMessage = 'Enrichissement terminé';
        this.loadResults();
      },
      error: () => {
        this.statusMessage = 'Erreur enrichissement';
        this.loading = false;
      },
      complete: () => this.loading = false
    });
  }

  // ─── Chargement des résultats ────────────────────────────

  loadResults() {
    this.http.get<Company[]>(`${this.api}/enrich/results`).subscribe({
      next: (data) => {
        this.companies       = data;
        this.availableCities = [...new Set(data.map(c => c.ville).filter(Boolean))];
      },
      error: () => this.statusMessage += ' (aucun résultat)'
    });
  }
}