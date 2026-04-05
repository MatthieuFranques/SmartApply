export interface JobOffer {
  title: string;
  url: string;
  description: string;
  tech_required: string[];
  relevance_score: number;
}

export interface ContactFormField {
  type?: string;
  name?: string;
  label?: string;
}

export interface ContactForm {
  url: string;
  has_file_upload: boolean;
  // CHANGEMENT ICI : On accepte les objets de champs
  fields: ContactFormField[] | any[]; 
  email_found: string;
}

export interface Company {
  // Champs de base (toujours présents)
  nom: string;
  domaine: string;
  ville: string;
  secteur: string;
  
  // Champs optionnels (ajout du ? pour la sécurité)
  careers_url?: string;
  site_title?: string;
  description?: string;
  about_text?: string;
  tech_keywords?: string[];
  job_keywords?: string[];
  job_titles_found?: string[];
  key_phrases?: string[];
  company_size_hint?: string;
  founded_hint?: string;
  is_recruiting?: boolean; // Optionnel car peut être null en DB
  job_offers?: JobOffer[];
  contact_form?: ContactForm;
  scrape_status?: string;
  scrape_error?: string;
  
  // Identifiant MongoDB (souvent utile pour le trackBy ou les détails)
  _id?: string; 
}