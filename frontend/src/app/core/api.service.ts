import { HttpErrorResponse } from '@angular/common/http';
import { Injectable, inject } from '@angular/core';
import { catchError, Observable, throwError } from 'rxjs';

import { ApiError } from './models';

@Injectable({ providedIn: 'root' })
export class ApiService {
  protected readonly base = '';

  protected handleError<T>(source: Observable<T>): Observable<T> {
    return source.pipe(
      catchError((err: HttpErrorResponse): Observable<T> => {
        let message = 'Erro inesperado. Tente novamente.';
        if (err.status === 0) {
          message = 'Não foi possível conectar ao servidor.';
        } else if (err.status === 502 || err.status === 503 || err.status === 504) {
          // Resposta do nginx/proxy (HTML cru), não da API: mensagem amigável
          // em vez de despejar o "502 Bad Gateway" na tela.
          message = 'O servidor está iniciando ou temporariamente indisponível. Tente novamente em instantes.';
        } else {
          const detail = (err.error as ApiError | undefined)?.detail;
          if (detail) {
            message = detail;
          } else if (typeof err.error === 'string' && err.error && !err.error.trimStart().startsWith('<')) {
            message = err.error;
          }
        }
        return throwError(() => new Error(message));
      }),
    );
  }
}
