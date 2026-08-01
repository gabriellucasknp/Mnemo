import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';
import { FormsModule } from '@angular/forms';

import { AulasService } from '../../core/aulas.service';
import { SimuladosService } from '../../core/simulados.service';
import { formatarData } from '../../core/format';
import { Aula, Simulado } from '../../core/models';
import { IconComponent } from '../../shared/icon/icon.component';
import { ProcessingOverlayComponent } from '../../shared/processing-overlay/processing-overlay';

@Component({
  selector: 'app-simulados',
  imports: [RouterLink, FormsModule, IconComponent, ProcessingOverlayComponent],
  templateUrl: './simulados.html',
  styleUrl: './simulados.scss',
})
export class SimuladosComponent implements OnInit {
  simulados: Simulado[] = [];
  aulas: Aula[] = [];
  erro: string | null = null;
  carregando = true;

  aulaSelecionada = '';
  titulo = '';
  quantidade = 10;
  processando = false;

  protected readonly formatarData = formatarData;

  constructor(
    private readonly aulasService: AulasService,
    private readonly simuladosService: SimuladosService,
    private readonly route: ActivatedRoute,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.simuladosService.listar().subscribe({
      next: (simulados) => {
        this.simulados = simulados;
        this.carregando = false;
      },
      error: (err) => {
        this.erro = err.message;
        this.carregando = false;
      },
    });

    this.aulasService.listar().subscribe({
      next: (aulas) => {
        this.aulas = aulas;
        const preselecionada = this.route.snapshot.queryParamMap.get('criar');
        if (preselecionada && aulas.some((a) => a.id === Number(preselecionada))) {
          this.aulaSelecionada = preselecionada;
        }
      },
      error: () => undefined,
    });
  }

  get opcoesAula(): Aula[] {
    return this.aulas.filter((a) => a.flashcards_count > 0);
  }

  get aulasComFlashcards(): Aula[] {
    return this.opcoesAula;
  }

  criar(): void {
    const aulaId = Number(this.aulaSelecionada);
    if (!aulaId) {
      this.erro = 'Selecione uma aula com flashcards para criar o simulado.';
      return;
    }

    this.erro = null;
    this.processando = true;

    this.simuladosService
      .criar({
        aula_id: aulaId,
        titulo: this.titulo.trim() || null,
        quantidade: this.quantidade,
      })
      .subscribe({
        next: (simulado) => this.router.navigate(['/simulados', simulado.id]),
        error: (err) => {
          this.erro = err.message;
          this.processando = false;
        },
      });
  }

  excluir(simulado: Simulado, event: MouseEvent): void {
    event.preventDefault();
    event.stopPropagation();
    const confirma = window.confirm(`Excluir o simulado "${simulado.titulo}"?`);
    if (!confirma) {
      return;
    }
    this.simuladosService.excluir(simulado.id).subscribe({
      next: () => {
        this.simulados = this.simulados.filter((s) => s.id !== simulado.id);
      },
      error: (err) => (this.erro = err.message),
    });
  }
}
