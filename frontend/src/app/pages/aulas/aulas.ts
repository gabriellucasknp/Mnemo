import { Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AulasService } from '../../core/aulas.service';
import { formatarData, minutosDuracao, tempoDecorrido } from '../../core/format';
import { Aula } from '../../core/models';
import { IconComponent } from '../../shared/icon/icon.component';

@Component({
  selector: 'app-aulas',
  imports: [RouterLink, IconComponent],
  templateUrl: './aulas.html',
  styleUrl: './aulas.scss',
})
export class AulasComponent implements OnInit {
  aulas: Aula[] = [];
  erro: string | null = null;
  carregando = true;

  protected readonly formatarData = formatarData;
  protected readonly minutosDuracao = minutosDuracao;
  protected readonly tempoDecorrido = tempoDecorrido;

  constructor(private readonly aulasService: AulasService) {}

  ngOnInit(): void {
    this.aulasService.listar().subscribe({
      next: (aulas) => {
        this.aulas = aulas;
        this.carregando = false;
      },
      error: (err) => {
        this.erro = err.message;
        this.carregando = false;
      },
    });
  }
}
