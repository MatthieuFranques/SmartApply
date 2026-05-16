import { Component, Input, Output, EventEmitter, OnChanges, SimpleChanges } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

import { ProfileService, UserProfile, PipelineSuggestion } from '../../services/profile.service';

@Component({
  selector:    'app-profile',
  standalone:  true,
  imports:     [CommonModule, FormsModule],
  templateUrl: './profile.component.html',
  styleUrls:   ['./profile.component.scss'],
})
export class ProfileComponent implements OnChanges {
  @Input()  visible = false;
  @Output() closed        = new EventEmitter<void>();
  @Output() launchPipeline = new EventEmitter<PipelineSuggestion>();

  activeTab: 'profile' | 'letter' = 'profile';

  profile: UserProfile = {
    prenom_nom: '', titre: '', email: '', telephone: '', ville: '',
    portfolio: '', github: '', diplome: '', ecole: '', annee: '',
    experiences: '', projet_phare: '', competences: '', soft_skills: '',
    recherche: '', reference_letter: '',
  };

  saving      = false;
  saved       = false;
  saveError   = '';
  cvLoading   = false;
  cvError     = '';
  suggestion: PipelineSuggestion | null = null;
  dragOver    = false;

  constructor(private readonly profileSvc: ProfileService) {}

  ngOnChanges(changes: SimpleChanges): void {
    if (changes['visible']?.currentValue === true) {
      this.loadProfile();
    }
  }

  private loadProfile(): void {
    this.profileSvc.getProfile().subscribe({
      next:  (p) => { this.profile = p; },
      error: () => {},
    });
  }

  save(): void {
    this.saving    = true;
    this.saveError = '';
    this.profileSvc.updateProfile(this.profile).subscribe({
      next: () => {
        this.saving = false;
        this.saved  = true;
        setTimeout(() => { this.saved = false; }, 2000);
      },
      error: () => {
        this.saving    = false;
        this.saveError = 'Erreur lors de la sauvegarde';
      },
    });
  }

  close(): void {
    this.closed.emit();
    this.suggestion = null;
    this.cvError    = '';
    this.saveError  = '';
  }

  // ── CV drag & drop ───────────────────────────────────────────

  onDragOver(e: DragEvent): void { e.preventDefault(); this.dragOver = true; }
  onDragLeave(): void { this.dragOver = false; }

  onDrop(e: DragEvent): void {
    e.preventDefault();
    this.dragOver = false;
    const file = e.dataTransfer?.files?.[0];
    if (file) this.analyzeCV(file);
  }

  onFileInput(e: Event): void {
    const file = (e.target as HTMLInputElement).files?.[0];
    if (file) this.analyzeCV(file);
  }

  analyzeCV(file: File): void {
    if (file.type !== 'application/pdf') {
      this.cvError = 'Fichier PDF uniquement';
      return;
    }
    this.cvLoading  = true;
    this.cvError    = '';
    this.suggestion = null;

    this.profileSvc.analyzeCV(file).subscribe({
      next: (res) => {
        this.cvLoading = false;
        this.profile   = { ...this.profile, ...res.profile };
        this.suggestion = res.pipeline_suggestion;
      },
      error: (err) => {
        this.cvLoading = false;
        const detail = err?.error?.detail || '';
        this.cvError = detail
          ? `Erreur : ${detail}`
          : 'Erreur analyse CV — vérifier que Ollama tourne (ollama serve)';
      },
    });
  }

  openPipeline(): void {
    if (this.suggestion) {
      this.launchPipeline.emit(this.suggestion);
      this.close();
    }
  }

  get profileCompletion(): number {
    const fields: (keyof UserProfile)[] = [
      'prenom_nom', 'email', 'ville', 'diplome', 'ecole',
      'experiences', 'competences', 'recherche',
    ];
    const filled = fields.filter(f => this.profile[f]?.trim()).length;
    return Math.round((filled / fields.length) * 100);
  }

  get letterWordCount(): number {
    return this.profile.reference_letter.trim().split(/\s+/).filter(Boolean).length;
  }
}
