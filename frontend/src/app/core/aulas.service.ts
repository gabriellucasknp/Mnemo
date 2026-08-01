import { HttpClient, HttpEvent, HttpEventType, HttpRequest } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable, filter, map } from 'rxjs';

import { ApiService } from './api.service';
import { Aula, AulaDetalhe, Health, HealthDb } from './models';

export interface UploadProgress {
  percent: number;
  state: 'enviando' | 'processando';
}

@Injectable({ providedIn: 'root' })
export class AulasService extends ApiService {
  private readonly http = inject(HttpClient);

  listar(): Observable<Aula[]> {
    return this.handleError(this.http.get<Aula[]>(`${this.base}/api/aulas`));
  }

  detalhar(id: number): Observable<AulaDetalhe> {
    return this.handleError(this.http.get<AulaDetalhe>(`${this.base}/api/aulas/${id}`));
  }

  excluir(id: number): Observable<void> {
    return this.handleError(this.http.delete<void>(`${this.base}/api/aulas/${id}`));
  }

  gerarFlashcards(id: number): Observable<AulaDetalhe> {
    return this.handleError(
      this.http.post<AulaDetalhe>(`${this.base}/api/aulas/${id}/flashcards`, {}),
    );
  }

  enviar(
    audio: File,
    titulo: string,
    onProgress?: (progresso: UploadProgress) => void,
  ): Observable<AulaDetalhe> {
    const form = new FormData();
    form.append('audio', audio, audio.name);
    if (titulo.trim()) {
      form.append('titulo', titulo.trim());
    }

    const req = new HttpRequest<FormData>('POST', `${this.base}/api/aulas`, form, {
      reportProgress: true,
    });

    return this.handleError(
      this.http.request<AulaDetalhe>(req).pipe(
        filter((event: HttpEvent<AulaDetalhe>): boolean => {
          if (event.type === HttpEventType.UploadProgress && event.total) {
            onProgress?.({
              percent: Math.round((event.loaded / event.total) * 100),
              state: 'enviando',
            });
          }
          return event.type === HttpEventType.Response;
        }),
        map((event: HttpEvent<AulaDetalhe>) => (event as { body: AulaDetalhe }).body),
      ),
    );
  }

  health(): Observable<Health> {
    return this.handleError(this.http.get<Health>(`${this.base}/health`));
  }

  healthDb(): Observable<HealthDb> {
    return this.handleError(this.http.get<HealthDb>(`${this.base}/health/db`));
  }
}
