import { Component, OnInit, OnDestroy } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { Subscription } from 'rxjs';

import { Company } from '../../models/company.model';
import { CompanyDetailComponent } from '../company/company.detail.component';
import { ApplicationsComponent } from '../applications/applications.component';
import { PipelineComponent } from '../../components/pipeline/pipeline.component';
import { PipelineService } from '../../services/pipeline.service';

@Component({
  selector: 'app-dashboard',
  standalone: true,
  imports: [
    CommonModule,
    FormsModule,
    CompanyDetailComponent,
    ApplicationsComponent,
    PipelineComponent,      
  ],
  templateUrl: './dashboard.component.html',
  styleUrls:   ['./dashboard.component.scss'],
})
export class DashboardComponent implements OnInit, OnDestroy {

  activeTab       : 'companies' | 'applications' = 'companies';
  companies       : Company[]  = [];
  loading         : boolean    = false;
  statusMessage   : string     = '';
  selectedCity    : string     = 'all';
  availableCities : string[]   = [];
  selectedCompany : any        = null;

  // ── Auth ──────────────────────────────────────────────────
  authenticated : boolean = false;
  authChecking  : boolean = true;
  currentUser   : { email: string; name: string } | null = null;

  private api = 'http://localhost:8000';
  private sub?: Subscription;

  constructor(
    private http:     HttpClient,
    private pipeline: PipelineService,
  ) {}

  ngOnInit():    void { this.checkAuth(); }
  ngOnDestroy(): void { this.sub?.unsubscribe(); }

  // ── Auth ──────────────────────────────────────────────────

  checkAuth(): void {
    this.authChecking = true;
    this.http.get<{ authenticated: boolean; email: string; name: string }>(
      `${this.api}/gmail/status`,
      { withCredentials: true },
    ).subscribe({
      next: (res) => {
        this.authenticated = res.authenticated;
        this.currentUser   = { email: res.email, name: res.name };
        this.authChecking  = false;
        if (this.authenticated) this.loadResults();
      },
      error: () => {
        this.authenticated = false;
        this.authChecking  = false;
      },
    });
  }

  connectGmail(): void {
    window.location.href = `${this.api}/gmail/auth`;
  }

  logout(): void {
    this.http.post(`${this.api}/gmail/logout`, {}, { withCredentials: true }).subscribe({
      next: () => {
        this.authenticated = false;
        this.currentUser   = null;
        this.companies     = [];
        this.sub?.unsubscribe();
      },
    });
  }

  // ── Stats calculées ───────────────────────────────────────

  get filteredCompanies(): Company[] {
    if (this.selectedCity === 'all') return this.companies;
    return this.companies.filter(c =>
      c.ville?.toLowerCase() === this.selectedCity.toLowerCase()
    );
  }

  get recruiting():  number { return this.filteredCompanies.filter(c => c.is_recruiting).length; }
  get withOffers():  number { return this.filteredCompanies.filter(c => c.job_offers?.length).length; }
  get withContact(): number { return this.filteredCompanies.filter(c => c.contact_form?.url).length; }

  filterByCity(city: string): void { this.selectedCity = city; }

  countByCity(city: string): number {
    return this.companies.filter(c =>
      c.ville?.toLowerCase() === city.toLowerCase()
    ).length;
  }

  openDetail(company: any):  void { this.selectedCompany = company; }
  closeDetail():             void { this.selectedCompany = null; }
  onDeleted(nom: string):    void {
    this.companies      = this.companies.filter(c => c.nom !== nom);
    this.selectedCompany = null;
  }

  // ── Callback du pipeline — recharge les résultats ────────
  // Appelé par (pipelineDone) depuis le template
  onPipelineDone(): void {
    this.loadResults();
  }

  // ── Chargement des résultats depuis la DB ─────────────────
  loadResults(): void {
    this.loading = true;
    this.http.get<Company[]>(
      `${this.api}/enrich/results`,
      { withCredentials: true },
    ).subscribe({
      next: (data) => {
        this.companies       = data;
        this.availableCities = [...new Set(data.map(c => c.ville).filter(Boolean))];
        this.loading         = false;
      },
      error: (err) => this.handleError(err, 'chargement'),
    });
  }

  // ── Gestion erreurs centralisée ───────────────────────────
  private handleError(err: any, context: string): void {
    this.loading = false;
    if (err.status === 401) {
      this.authenticated = false;
      this.statusMessage = 'Session expirée — reconnecte-toi';
    } else {
      this.statusMessage = `Erreur ${context} (${err.status})`;
    }
  }
}