import { Component } from '@angular/core';
import { CommonModule } from '@angular/common';
import { RouterLink } from '@angular/router';

interface Step {
  title: string;
  text: string;
}

interface Feature {
  title: string;
  text: string;
}

@Component({
  selector: 'app-landing',
  standalone: true,
  imports: [CommonModule, RouterLink],
  templateUrl: './landing.component.html',
  styleUrls: ['./landing.component.scss'],
})
export class LandingComponent {
  readonly steps: Step[] = [
    { title: 'Scraping',       text: 'Récupère les entreprises par ville et secteur d\'activité.' },
    { title: 'Filtrage',       text: 'Score la pertinence via DNS, site web et mots-clés.' },
    { title: 'Enrichissement', text: 'Analyse les sites pour détecter l\'activité et les signaux de recrutement.' },
    { title: 'Lettres & emails', text: 'Génère tes lettres de motivation et des brouillons d\'email prêts à envoyer.' },
  ];

  readonly features: Feature[] = [
    { title: 'Pipeline automatisé', text: 'Du scraping à la lettre, tout s\'enchaîne en streaming temps réel.' },
    { title: 'Ciblage pertinent',   text: 'Ne garde que les entreprises qui correspondent à ton profil.' },
    { title: 'Lettres & brouillons', text: 'Génère lettres de motivation et brouillons d\'email Gmail en un clic.' },
    { title: 'Suivi Gmail',          text: 'Synchronise tes candidatures envoyées, relancées et refusées.' },
  ];
}
