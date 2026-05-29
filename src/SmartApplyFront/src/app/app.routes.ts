import { Routes } from '@angular/router';
import { LandingComponent } from './pages/landing/landing.component';
import { DashboardComponent } from './pages/dashboard/dashboard.component';

export const routes: Routes = [
  { path: '',    component: LandingComponent },
  { path: 'app', component: DashboardComponent },
  { path: '**',  redirectTo: '' },
];
