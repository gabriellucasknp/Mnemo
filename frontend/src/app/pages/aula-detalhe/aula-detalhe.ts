import { Component, OnInit } from '@angular/core';
import { ActivatedRoute, Router, RouterLink } from '@angular/router';

import { AulasService } from '../../core/aulas.service';
import { formatarData, minutosDuracao } from '../../core/format';
import { AulaDetalhe, CategoriaFlashcard, Flashcard } from '../../core/models';
import { IconComponent } from '../../shared/icon/icon.component';

@Component({
  selector: 'app-aula-detalhe',
  imports: [RouterLink, IconComponent],
  templateUrl: './aula-detalhe.html',
  styleUrl: './aula-detalhe.scss',
})
export class AulaDetalheComponent implements OnInit {
  aula: AulaDetalhe | null = null;
  erro: string | null = null;
  carregando = true;

  gerando = false;
  excluindo = false;

  modoEstudo = false;
  modoConcluido = false;
  idx = 0;
  virado = false;
  acertos = 0;
  erros = 0;

  protected readonly formatarData = formatarData;
  protected readonly minutosDuracao = minutosDuracao;

  constructor(
    private readonly route: ActivatedRoute,
    private readonly router: Router,
    private readonly aulasService: AulasService,
  ) {}

  ngOnInit(): void {
    this.route.paramMap.subscribe((params) => {
      const id = Number(params.get('id'));
      if (Number.isNaN(id)) {
        this.erro = 'Aula inválida';
        this.carregando = false;
        return;
      }
      this.carregarAula(id);
    });
  }

  private carregarAula(id: number): void {
    this.carregando = true;
    this.aulasService.detalhar(id).subscribe({
      next: (aula) => {
        this.aula = aula;
        this.carregando = false;
      },
      error: (err) => {
        this.erro = err.message;
        this.carregando = false;
      },
    });
  }

  get flashcards(): Flashcard[] {
    return this.aula?.flashcards ?? [];
  }

  classeCategoria(categoria: CategoriaFlashcard): string {
    switch (categoria) {
      case 'conceito':
        return 'conceito';
      case 'definição':
        return 'definicao';
      case 'processo':
        return 'processo';
      case 'exemplo':
        return 'exemplo';
      default:
        return 'conceito';
    }
  }

  get cartaAtual(): Flashcard | null {
    return this.flashcards[this.idx] ?? null;
  }

  get barraLargura(): string {
    const total = this.flashcards.length;
    if (!total) {
      return '0%';
    }
    return `${Math.round((this.idx / total) * 100)}%`;
  }

  iniciarEstudo(): void {
    this.idx = 0;
    this.acertos = 0;
    this.erros = 0;
    this.virado = false;
    this.modoConcluido = false;
    this.modoEstudo = true;
  }

  fecharEstudo(): void {
    this.modoEstudo = false;
    this.modoConcluido = false;
  }

  virarCarta(): void {
    if (!this.cartaAtual) {
      return;
    }
    this.virado = !this.virado;
  }

  responder(lembrou: boolean): void {
    if (lembrou) {
      this.acertos++;
    } else {
      this.erros++;
    }
    if (this.idx + 1 >= this.flashcards.length) {
      this.modoEstudo = false;
      this.modoConcluido = true;
      return;
    }
    this.idx++;
    this.virado = false;
  }

  gerarFlashcards(): void {
    if (!this.aula) {
      return;
    }
    this.gerando = true;
    this.aulasService.gerarFlashcards(this.aula.id).subscribe({
      next: (aula) => {
        this.aula = aula;
        this.gerando = false;
      },
      error: (err) => {
        this.erro = err.message;
        this.gerando = false;
      },
    });
  }

  excluirAula(): void {
    if (!this.aula) {
      return;
    }
    const confirma = window.confirm(
      `Excluir a aula "${this.aula.titulo}" e todos os flashcards vinculados?`,
    );
    if (!confirma) {
      return;
    }
    this.excluindo = true;
    this.aulasService.excluir(this.aula.id).subscribe({
      next: () => this.router.navigate(['/aulas']),
      error: (err) => {
        this.erro = err.message;
        this.excluindo = false;
      },
    });
  }

  criarSimulado(): void {
    if (!this.aula) {
      return;
    }
    this.router.navigate(['/simulados'], {
      queryParams: { criar: this.aula.id },
    });
  }
}
