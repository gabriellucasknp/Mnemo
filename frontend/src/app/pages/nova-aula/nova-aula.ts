import { Component, ElementRef, OnInit, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AulasService, UploadProgress } from '../../core/aulas.service';
import { formatarData, minutosDuracao } from '../../core/format';
import { Aula } from '../../core/models';
import { IconComponent } from '../../shared/icon/icon.component';
import { ProcessingOverlayComponent } from '../../shared/processing-overlay/processing-overlay';

@Component({
  selector: 'app-nova-aula',
  imports: [RouterLink, FormsModule, IconComponent, ProcessingOverlayComponent],
  templateUrl: './nova-aula.html',
  styleUrl: './nova-aula.scss',
})
export class NovaAulaComponent implements OnInit {
  @ViewChild('inputAudio') inputAudio!: ElementRef<HTMLInputElement>;

  arquivo: File | null = null;
  titulo = '';
  erro: string | null = null;
  processando = false;
  arrastando = false;
  progressoUpload: UploadProgress | null = null;
  passoAtivo = 0;

  aulas: Aula[] = [];

  protected readonly formatarData = formatarData;
  protected readonly minutosDuracao = minutosDuracao;

  constructor(
    private readonly aulasService: AulasService,
    private readonly router: Router,
  ) {}

  ngOnInit(): void {
    this.carregarAulas();
  }

  private carregarAulas(): void {
    this.aulasService.listar().subscribe({
      next: (aulas) => (this.aulas = aulas),
      error: () => undefined,
    });
  }

  aoSelecionarArquivo(event: Event): void {
    const input = event.target as HTMLInputElement;
    const arquivo = input.files?.[0];
    if (arquivo) {
      this.arquivo = arquivo;
      this.erro = null;
    }
  }

  aoSoltarArquivo(event: DragEvent): void {
    event.preventDefault();
    const arquivo = event.dataTransfer?.files?.[0];
    if (arquivo) {
      this.arquivo = arquivo;
      this.erro = null;
    }
  }

  clicarDropzone(): void {
    this.inputAudio?.nativeElement.click();
  }

  limparArquivo(): void {
    this.arquivo = null;
    if (this.inputAudio) {
      this.inputAudio.nativeElement.value = '';
    }
  }

  enviar(): void {
    if (!this.arquivo) {
      return;
    }

    this.erro = null;
    this.processando = true;
    this.passoAtivo = 0;
    this.progressoUpload = null;

    const avancaPassos = setInterval(() => {
      if (this.passoAtivo < 2) {
        this.passoAtivo++;
      }
    }, 20000);

    this.aulasService
      .enviar(this.arquivo, this.titulo, (p) => (this.progressoUpload = p))
      .subscribe({
        next: (aula) => {
          clearInterval(avancaPassos);
          this.router.navigate(['/aulas', aula.id]);
        },
        error: (err) => {
          clearInterval(avancaPassos);
          this.erro = err.message;
          this.processando = false;
        },
      });
  }
}
