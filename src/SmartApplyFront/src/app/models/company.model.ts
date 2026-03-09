export interface JobOffer {
  title: string;
  url: string;
  description: string;
  tech_required: string[];
  relevance_score: number;
}

export interface ContactForm {
  url: string;
  has_file_upload: boolean;
  fields: string[];
  email_found: string;
}

export interface Company {
  nom: string;
  domaine: string;
  ville: string;
  secteur: string;
  careers_url: string;
  site_title: string;
  description: string;
  about_text: string;
  tech_keywords: string[];
  job_keywords: string[];
  job_titles_found: string[];
  key_phrases: string[];
  company_size_hint: string;
  founded_hint: string;
  is_recruiting: boolean;
  job_offers: JobOffer[];
  contact_form: ContactForm;
  scrape_status: string;
  scrape_error: string;
}