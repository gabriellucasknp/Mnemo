import { Routes } from '@angular/router';

export const routes: Routes = [
  {
    path: '',
    pathMatch: 'full',
    loadComponent: () => import('./pages/dashboard/dashboard').then((m) => m.DashboardComponent),
  },
  {
    path: 'nova-aula',
    loadComponent: () => import('./pages/nova-aula/nova-aula').then((m) => m.NovaAulaComponent),
  },
  {
    path: 'aulas',
    loadComponent: () => import('./pages/aulas/aulas').then((m) => m.AulasComponent),
  },
  {
    path: 'aulas/:id',
    loadComponent: () =>
      import('./pages/aula-detalhe/aula-detalhe').then((m) => m.AulaDetalheComponent),
  },
  {
    path: 'simulados',
    loadComponent: () =>
      import('./pages/simulados/simulados').then((m) => m.SimuladosComponent),
  },
  {
    path: 'simulados/:id',
    loadComponent: () =>
      import('./pages/simulado-detalhe/simulado-detalhe').then((m) => m.SimuladoDetalheComponent),
  },
  {
    path: '**',
    redirectTo: '',
  },
];
