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
        } else if (typeof err.error === 'string' && err.error) {
          message = err.error;
        } else {
          const detail = (err.error as ApiError | undefined)?.detail;
          if (detail) {
            message = detail;
          }
        }
        return throwError(() => new Error(message));
      }),
    );
  }
}
