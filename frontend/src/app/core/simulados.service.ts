import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ApiService } from './api.service';
import { ResultadoSimulado, Simulado } from './models';

export interface CriarSimulado {
  aula_id: number;
  titulo?: string | null;
  quantidade: number;
}

@Injectable({ providedIn: 'root' })
export class SimuladosService extends ApiService {
  private readonly http = inject(HttpClient);

  listar(): Observable<Simulado[]> {
    return this.handleError(this.http.get<Simulado[]>(`${this.base}/api/simulados`));
  }

  detalhar(id: number): Observable<Simulado> {
    return this.handleError(this.http.get<Simulado>(`${this.base}/api/simulados/${id}`));
  }

  criar(dados: CriarSimulado): Observable<Simulado> {
    return this.handleError(this.http.post<Simulado>(`${this.base}/api/simulados`, dados));
  }

  responder(id: number, respostas: Record<number, string>): Observable<ResultadoSimulado> {
    return this.handleError(
      this.http.post<ResultadoSimulado>(`${this.base}/api/simulados/${id}/responder`, {
        respostas,
      }),
    );
  }

  excluir(id: number): Observable<void> {
    return this.handleError(this.http.delete<void>(`${this.base}/api/simulados/${id}`));
  }
}
