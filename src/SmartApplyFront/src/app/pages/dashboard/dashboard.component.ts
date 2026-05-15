import { Component, OnInit, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { Subscription } from 'rxjs';

import { Company } from '../../models/company.model';
import { CompanyDetailComponent } from '../company/company.detail.component';
import { ApplicationsComponent } from '../applications/applications.component';
import { OffersComponent } from '../offers/offers.component';
import { PipelineComponent } from '../../components/pipeline/pipeline.component';
import { ProfileComponent } from '../../components/profile/profile.component';
import { AuthScreenComponent } from '../../components/authScreen/auth-screen.component';
import { StatsBarComponent, StatItem } from '../../components/statsBar/stats-bar.component';
import { CityFiltersComponent, CityCount } from '../../components/cityFilters/city-filters.component';
import { CompanyTableComponent } from '../../components/companyTable/company-table.component';
import { PipelineSuggestion } from '../../services/profile.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    CompanyDetailComponent,
    ApplicationsComponent,
    OffersComponent,
    PipelineComponent,
    ProfileComponent,
    AuthScreenComponent,
    StatsBarComponent,
    CityFiltersComponent,
    CompanyTableComponent,
  ],
  templateUrl: './dashboard.component.html',
  styleUrls:   ['./dashboard.component.scss'],
})
export class DashboardComponent implements OnInit, OnDestroy {

  activeTab          : 'companies' | 'applications' | 'offers' = 'companies';
  showPipeline       : boolean = false;
  showProfile        : boolean = false;
  pipelineSuggestion : PipelineSuggestion | null = null;

  companies       : Company[]  = [];
  loading         : boolean    = false;
  statusMessage   : string     = '';
  selectedCity    : string     = 'all';
  selectedCompany : Company | null = null;

  authenticated : boolean = false;
  authChecking  : boolean = true;
  currentUser: { email: string; name: string } | null = null;
  private readonly api = 'http://localhost:8000';
  private readonly sub?: Subscription;

  constructor(private readonly http: HttpClient) {}

  ngOnInit():    void { this.checkAuth(); }
  ngOnDestroy(): void { this.sub?.unsubscribe(); }

  // ── Auth ──────────────────────────────────────────────────

  checkAuth(): void {
    this.authChecking = true;
    this.http.get<{ authenticated: boolean; email: string; name: string }>(
      `${this.api}/auth/status`, { withCredentials: true },
    ).subscribe({
      next: (res) => {
        this.authenticated = res.authenticated;
        this.currentUser   = { email: res.email, name: res.name };
        this.authChecking  = false;
        if (this.authenticated) this.loadResults();
      },
      error: () => { this.authenticated = false; this.authChecking = false; },
    });
  }

  connectGmail(): void { globalThis.location.href = `${this.api}/auth/login`; }

  logout(): void {
    this.http.post(`${this.api}/auth/logout`, {}, { withCredentials: true }).subscribe({
      next: () => {
        this.authenticated = false;
        this.currentUser   = null;
        this.companies     = [];
      },
    });
  }

  // ── Computed ──────────────────────────────────────────────

  get filteredCompanies(): Company[] {
    if (!this.selectedCity || this.selectedCity === 'all') return this.companies;
    return this.companies.filter(c =>
      c.ville?.toLowerCase().trim() === this.selectedCity.toLowerCase().trim()
    );
  }

  get statItems(): StatItem[] {
    const fc = this.filteredCompanies;
    return [
      { value: fc.length,                                     label: 'Entreprises', color: 'var(--accent)'  },
      { value: fc.filter(c => c.is_recruiting).length,        label: 'Recrutent',   color: 'var(--accent5)' },
      { value: fc.filter(c => !!c.contact_form?.url).length,  label: 'Contacts',    color: 'var(--accent2)' },
    ];
  }

  get cityItems(): CityCount[] {
    return [...new Set(this.companies.map(c => c.ville).filter(Boolean))]
      .map(name => ({
        name,
        count: this.companies.filter(c => c.ville?.toLowerCase() === name.toLowerCase()).length,
      }));
  }

  // ── Actions ───────────────────────────────────────────────

  filterByCity(city: string): void { this.selectedCity = city; }
  openDetail(company: Company):  void { this.selectedCompany = company; }
  closeDetail():                 void { this.selectedCompany = null; }

  onDeleted(nom: string): void {
    this.companies       = this.companies.filter(c => c.nom !== nom);
    this.selectedCompany = null;
  }

  onPipelineDone(): void { this.loadResults(); }

  onLaunchPipeline(suggestion: PipelineSuggestion): void {
    this.pipelineSuggestion = suggestion;
    this.showPipeline = true;
  }

  // ── Load ──────────────────────────────────────────────────

  loadResults(): void {
    this.loading = true;
    this.statusMessage = 'Chargement des données...';
    this.http.get<Company[]>(`${this.api}/enrich/results`, { withCredentials: true }).subscribe({
      next: (data) => {
        this.companies     = [...data];
        this.loading       = false;
        this.statusMessage = '';
      },
      error: (err) => {
        this.loading = false;
        this.statusMessage = err.status === 401
          ? 'Session expirée — reconnecte-toi'
          : `Erreur chargement (${err.status})`;
        if (err.status === 401) this.authenticated = false;
      },
    });
  }
}
