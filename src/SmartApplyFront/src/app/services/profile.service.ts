import { Injectable } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { Observable } from 'rxjs';

export interface UserProfile {
  prenom_nom:       string;
  titre:            string;
  email:            string;
  telephone:        string;
  ville:            string;
  portfolio:        string;
  github:           string;
  diplome:          string;
  ecole:            string;
  annee:            string;
  experiences:      string;
  projet_phare:     string;
  competences:      string;
  soft_skills:      string;
  recherche:        string;
  reference_letter: string;
}

export interface PipelineSuggestion {
  cities:        string[];
  sectors:       string[];
  keyword_match: string;
  max_results:   number;
  reasoning:     string;
}

export interface CVAnalysisResult {
  profile:             UserProfile;
  pipeline_suggestion: PipelineSuggestion;
}

@Injectable({ providedIn: 'root' })
export class ProfileService {
  private readonly api = 'http://localhost:8000';

  constructor(private readonly http: HttpClient) {}

  getProfile(): Observable<UserProfile> {
    return this.http.get<UserProfile>(`${this.api}/profile`, { withCredentials: true });
  }

  updateProfile(profile: UserProfile): Observable<{ ok: boolean }> {
    return this.http.put<{ ok: boolean }>(`${this.api}/profile`, profile, { withCredentials: true });
  }

  analyzeCV(file: File, model = 'mistral'): Observable<CVAnalysisResult> {
    const form = new FormData();
    form.append('file', file);
    return this.http.post<CVAnalysisResult>(`${this.api}/profile/cv?model=${model}`, form, { withCredentials: true });
  }
}
