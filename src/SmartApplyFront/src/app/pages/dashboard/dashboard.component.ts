import { Component, OnInit } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Company } from '../../models/company.model';
import { CompanyDetailComponent } from '../company/company.detail.component';
import { ApplicationsComponent } from '../applications/applications.component';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [CommonModule, FormsModule, CompanyDetailComponent, ApplicationsComponent],
  templateUrl: './dashboard.component.html',
  styleUrls: ['./dashboard.component.scss']
})
export class DashboardComponent implements OnInit {

  activeTab       : 'companies' | 'applications' = 'companies';
  city            : string   = 'Toulouse';
  companies       : Company[] = [];
  loading         : boolean  = false;
  statusMessage   : string   = '';
  selectedCity    : string   = 'all';
  availableCities : string[] = [];
  selectedCompany : any      = null;

  // ── Auth ──────────────────────────────────────────────────
  authenticated   : boolean  = false;
  authChecking    : boolean  = true;
  currentUser     : { email: string; name: string } | null = null;

  private api = 'http://localhost:8000';

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.checkAuth();
  }

  // ── Vérifie si le cookie de session est valide ────────────
  checkAuth(): void {
  this.authChecking = true;
  this.http.get<{ authenticated: boolean; email: string; name: string }>(
    `${this.api}/gmail/status`,
    { withCredentials: true } 
  ).subscribe({
    next: (res) => {
      this.authenticated = res.authenticated;
      this.currentUser = { email: res.email, name: res.name };
      this.authChecking = false;
      if (this.authenticated) this.loadResults();
    },
    error: () => {
      this.authenticated = false;
      this.authChecking = false;
    }
  });
}

  connectGmail(): void {
    window.location.href = `${this.api}/gmail/auth`;
  }

  logout(): void {
  this.http.post(`${this.api}/gmail/logout`, {}, { withCredentials: true }).subscribe({
    next: () => {
      this.authenticated = false;
      this.currentUser = null;
      this.companies = [];
    }
  });
}

  // ── Stats calculées ───────────────────────────────────────
  get filteredCompanies() {
    if (this.selectedCity === 'all') return this.companies;
    return this.companies.filter(c =>
      c.ville?.toLowerCase() === this.selectedCity.toLowerCase()
    );
  }

  get recruiting()  { return this.filteredCompanies.filter(c => c.is_recruiting).length; }
  get withOffers()  { return this.filteredCompanies.filter(c => c.job_offers?.length).length; }
  get withContact() { return this.filteredCompanies.filter(c => c.contact_form?.url).length; }

  filterByCity(city: string)  { this.selectedCity = city; }
  countByCity(city: string)   { return this.companies.filter(c => c.ville?.toLowerCase() === city.toLowerCase()).length; }
  openDetail(company: any)    { this.selectedCompany = company; }
  closeDetail()               { this.selectedCompany = null; }
  onDeleted(nom: string)      { this.companies = this.companies.filter(c => c.nom !== nom); this.selectedCompany = null; }

  // ── Pipeline — les requêtes envoient le cookie auto ──────
  onScrape() {
    this.loading = true;
    this.statusMessage = 'Scraping en cours...';
    this.http.post(`${this.api}/scraping/start`, { cities: [this.city] }).subscribe({
      next: () => { this.statusMessage = 'Scraping lancé ✅'; this.loading = false; },
      error: (err) => { this.handleError(err, 'scraping'); }
    });
  }

  onFilter() {
    this.loading = true;
    this.statusMessage = 'Filtrage en cours...';
    this.http.post(`${this.api}/filter/start`, { cities: [this.city] }).subscribe({
      next: () => { this.statusMessage = 'Filtrage terminé ✅'; this.loadResults(); },
      error: (err) => { this.handleError(err, 'filtrage'); }
    });
  }

  onEnrich() {
    this.loading = true;
    this.statusMessage = 'Enrichissement en cours...';
    this.http.post(`${this.api}/enrich/start`, {}).subscribe({
      next: () => { this.statusMessage = 'Enrichissement terminé ✅'; this.loadResults(); },
      error: (err) => { this.handleError(err, 'enrichissement'); }
    });
  }

  loadResults() {
  this.http.get<Company[]>(`${this.api}/enrich/results`, { withCredentials: true }).subscribe({
    next: (data) => {
      this.companies = data;
      this.availableCities = [...new Set(data.map(c => c.ville).filter(Boolean))];
      this.loading = false;
    },
    error: (err) => { this.handleError(err, 'chargement'); }
  });
}

  // ── Gestion erreurs centralisée ───────────────────────────
  private handleError(err: any, context: string): void {
    this.loading = false;
    if (err.status === 401) {
      // Session expirée → retour à l'écran de connexion
      this.authenticated = false;
      this.statusMessage = 'Session expirée — reconnecte-toi';
    } else {
      this.statusMessage = `Erreur ${context} (${err.status})`;
    }
  }
}