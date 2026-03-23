import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { HttpClient } from '@angular/common/http';

export interface Application {
  company: string;
  poste:   string;
  date:    string;
  status:  'envoye' | 'relance' | 'refuse';
  url?:    string;
}

@Component({
  selector: 'app-applications',
  standalone: true,
  imports: [CommonModule],
  templateUrl: './applications.component.html',
  styleUrls: ['./applications.component.scss']
})
export class ApplicationsComponent implements OnInit {

  applications: Application[] = [];
  loading      = false;
  error        = '';

  statuses     = ['tous', 'envoye', 'relance', 'refuse'];
  activeStatus = 'tous';

  private api = 'http://localhost:8000/applications'; // ← adapte à ta route FastAPI

  constructor(private http: HttpClient) {}

  ngOnInit(): void {
    this.loadApplications();
  }

  loadApplications(): void {
    this.loading = true;
    this.error   = '';
    this.http.get<Application[]>(this.api).subscribe({
      next:  (data) => { this.applications = data; this.loading = false; },
      error: ()     => { this.error = 'Impossible de charger les candidatures depuis Gmail.'; this.loading = false; }
    });
  }

  get filtered(): Application[] {
    if (this.activeStatus === 'tous') return this.applications;
    return this.applications.filter(a => a.status === this.activeStatus);
  }

  labelFor(status: string): string {
    const labels: Record<string, string> = {
      tous:    'TOUS',
      envoye:  'ENVOYÉ',
      relance: 'RELANCÉ',
      refuse:  'REFUSÉ',
    };
    return labels[status] ?? status;
  }
}
