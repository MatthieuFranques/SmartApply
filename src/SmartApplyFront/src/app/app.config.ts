import { ApplicationConfig, provideZoneChangeDetection } from '@angular/core';
import { provideRouter } from '@angular/router';
import { provideHttpClient, withInterceptors, HttpRequest, HttpHandlerFn } from '@angular/common/http';

import { routes } from './app.routes';

/**
 * Intercepteur pour ajouter withCredentials: true à toutes les requêtes.
 * Cela permet d'inclure les cookies (session, auth) dans les appels API.
 */
export function credentialsInterceptor(req: HttpRequest<unknown>, next: HttpHandlerFn) {
  const cloned = req.clone({ withCredentials: true });
  return next(cloned);
}

export const appConfig: ApplicationConfig = {
  providers: [
    provideZoneChangeDetection({ eventCoalescing: true }),
    provideRouter(routes),
    provideHttpClient(
        withInterceptors([credentialsInterceptor])
    )
  ]
};