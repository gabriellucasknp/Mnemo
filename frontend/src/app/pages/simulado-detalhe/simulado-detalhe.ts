import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { SimuladosService } from '../../core/simulados.service';
import { formatarData } from '../../core/format';
import { Questao, ResultadoSimulado, Simulado } from '../../core/models';
import { IconComponent } from '../../shared/icon/icon.component';

const LETRAS = ['A', 'B', 'C', 'D', 'E'];

interface QuestaoRevisao extends Questao {
  gabarito: string;
  marcada: string | null;
  acertou: boolean;
}

@Component({
  selector: 'app-simulado-detalhe',
  imports: [RouterLink, IconComponent],
  templateUrl: './simulado-detalhe.html',
  styleUrl: './simulado-detalhe.scss',
})
export class SimuladoDetalheComponent implements OnInit {
  simulado: Simulado | null = null;
  erro: string | null = null;
  carregando = true;

  respostas: Record<number, string> = {};
  idx = 0;
  enviando = false;
  resultado: ResultadoSimulado | null = null;
  excluindo = false;

  protected readonly formatarData = formatarData;
  protected readonly letras = LETRAS;

  constructor(
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly simuladosService: SimuladosService,
  ) {}

  ngOnInit(): void {
    this.route.paramMap.subscribe((params) => {
      const id = Number(params.get('id'));
      if (Number.isNaN(id)) {
        this.erro = 'Simulado inválido';
        this.carregando = false;
        return;
      }
      this.carregarSimulado(id);
    });
  }

  private carregarSimulado(id: number): void {
    this.carregando = true;
    this.simuladosService.detalhar(id).subscribe({
      next: (simulado) => {
        this.simulado = simulado;
        this.carregando = false;
      },
      error: (err) => {
        this.erro = err.message;
        this.carregando = false;
      },
    });
  }

  get questoes(): Questao[] {
    return this.simulado?.questoes ?? [];
  }

  get questaoAtual(): Questao | null {
    return this.questoes[this.idx] ?? null;
  }

  get respondidas(): number {
    return Object.keys(this.respostas).length;
  }

  get totalRespondidas(): number {
    return this.questoes.filter((q) => this.respostas[q.id]).length;
  }

  get todasRespondidas(): boolean {
    return this.questoes.length > 0 && this.totalRespondidas === this.questoes.length;
  }

  get barraLargura(): string {
    const total = this.questoes.length;
    if (!total) {
      return '0%';
    }
    return `${Math.round((this.respondidas / total) * 100)}%`;
  }

  responder(questao: Questao, alternativa: string): void {
    this.respostas[questao.id] = alternativa;
  }

  alternativaMarcada(questao: Questao, alternativa: string): boolean {
    return this.respostas[questao.id] === alternativa;
  }

  irPara(indice: number): void {
    if (indice >= 0 && indice < this.questoes.length) {
      this.idx = indice;
    }
  }

  proxima(): void {
    if (this.idx + 1 < this.questoes.length) {
      this.idx++;
    }
  }

  anterior(): void {
    if (this.idx > 0) {
      this.idx--;
    }
  }

  enviar(): void {
    if (!this.simulado || !this.todasRespondidas) {
      return;
    }
    this.enviando = true;
    this.simuladosService.responder(this.simulado.id, this.respostas).subscribe({
      next: (resultado) => {
        this.resultado = resultado;
        this.enviando = false;
        this.idx = 0;
      },
      error: (err) => {
        this.erro = err.message;
        this.enviando = false;
      },
    });
  }

  questoesRevisao(): QuestaoRevisao[] {
    if (!this.resultado) {
      return [];
    }
    const detalhes = this.resultado.detalhes;
    return this.questoes.map((q) => {
      const detalhe = detalhes.find((d) => d.questao_id === q.id);
      return {
        ...q,
        gabarito: detalhe?.gabarito ?? '',
        marcada: detalhe?.alternativa_marcada ?? null,
        acertou: detalhe?.acertou ?? false,
      };
    });
  }

  reiniciar(): void {
    this.respostas = {};
    this.idx = 0;
    this.resultado = null;
  }

  excluir(): void {
    if (!this.simulado) {
      return;
    }
    const confirma = window.confirm(`Excluir o simulado "${this.simulado.titulo}"?`);
    if (!confirma) {
      return;
    }
    this.excluindo = true;
    this.simuladosService.excluir(this.simulado.id).subscribe({
      next: () => this.router.navigate(['/simulados']),
      error: (err) => {
        this.erro = err.message;
        this.excluindo = false;
      },
    });
  }
}
