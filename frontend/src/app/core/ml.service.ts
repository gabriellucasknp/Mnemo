import { HttpClient } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { Observable } from 'rxjs';

import { ApiService } from './api.service';
import { Classificacao, MlQuestoesStatus, MlStatus } from './models';

@Injectable({ providedIn: 'root' })
export class MlService extends ApiService {
  private readonly http = inject(HttpClient);

  statusFlashcards(): Observable<MlStatus> {
    return this.handleError(this.http.get<MlStatus>(`${this.base}/api/ml/status`));
  }

  statusQuestoes(): Observable<MlQuestoesStatus> {
    return this.handleError(this.http.get<MlQuestoesStatus>(`${this.base}/api/ml/status-questoes`));
  }

  classificar(texto: string): Observable<Classificacao> {
    return this.handleError(
      this.http.post<Classificacao>(`${this.base}/api/ml/classificar`, { texto }),
    );
  }
}
