import { Component, ElementRef, OnDestroy, OnInit, ViewChild } from '@angular/core';
import { FormsModule } from '@angular/forms';
import { Router, RouterLink } from '@angular/router';

import { AulasService, UploadProgress } from '../../core/aulas.service';
import { formatarData, minutosDuracao } from '../../core/format';
import { Aula } from '../../core/models';
import { IconComponent } from '../../shared/icon/icon.component';
import { ProcessingOverlayComponent } from '../../shared/processing-overlay/processing-overlay';

type ModoNovaAula = 'gravar' | 'upload';

const MIMES_AUDIO = ['audio/webm;codecs=opus', 'audio/webm', 'audio/mp4', ''];

@Component({
  selector: 'app-nova-aula',
  imports: [RouterLink, FormsModule, IconComponent, ProcessingOverlayComponent],
  templateUrl: './nova-aula.html',
  styleUrl: './nova-aula.scss',
})
export class NovaAulaComponent implements OnInit, OnDestroy {
  @ViewChild('inputAudio') inputAudio!: ElementRef<HTMLInputElement>;

  modo: ModoNovaAula = 'upload';

  arquivo: File | null = null;
  titulo = '';
  erro: string | null = null;
  processando = false;
  arrastando = false;
  progressoUpload: UploadProgress | null = null;
  passoAtivo = 0;

  gravando = false;
  tempoGravacao = 0;
  blobAudio: Blob | null = null;
  urlAudio: string | null = null;
  private recorder: MediaRecorder | null = null;
  private streamAudio: MediaStream | null = null;
  private pedacosAudio: Blob[] = [];
  private timerGravacao: number | null = null;

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

  ngOnDestroy(): void {
    this.limparTimer();
    this.pararStream();
    if (this.urlAudio) {
      URL.revokeObjectURL(this.urlAudio);
    }
  }

  get tempoFormatado(): string {
    const min = Math.floor(this.tempoGravacao / 60);
    const seg = this.tempoGravacao % 60;
    return `${min.toString().padStart(2, '0')}:${seg.toString().padStart(2, '0')}`;
  }

  private carregarAulas(): void {
    this.aulasService.listar().subscribe({
      next: (aulas) => (this.aulas = aulas),
      error: () => undefined,
    });
  }

  trocarModo(modo: ModoNovaAula): void {
    if (modo === 'gravar' && this.gravando) {
      return;
    }
    this.modo = modo;
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

  async iniciarGravacao(): Promise<void> {
    if (this.gravando) {
      return;
    }
    this.erro = null;
    this.blobAudio = null;
    this.tempoGravacao = 0;

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      this.streamAudio = stream;

      const mime = MIMES_AUDIO.find((t) => t === '' || MediaRecorder.isTypeSupported(t)) ?? '';
      const recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);

      this.pedacosAudio = [];
      recorder.ondataavailable = (event: BlobEvent): void => {
        if (event.data.size > 0) {
          this.pedacosAudio.push(event.data);
        }
      };
      recorder.onstop = (): void => {
        const tipo = recorder.mimeType || 'audio/webm';
        this.blobAudio = new Blob(this.pedacosAudio, { type: tipo });
        if (this.urlAudio) {
          URL.revokeObjectURL(this.urlAudio);
        }
        this.urlAudio = URL.createObjectURL(this.blobAudio);
        this.pararStream();
      };

      this.recorder = recorder;
      recorder.start();
      this.gravando = true;
      this.limparTimer();
      this.timerGravacao = window.setInterval(() => {
        this.tempoGravacao++;
      }, 1000);
    } catch {
      this.erro = 'Não foi possível acessar o microfone. Verifique a permissão.';
    }
  }

  pararGravacao(): void {
    if (this.recorder && this.recorder.state !== 'inactive') {
      this.recorder.stop();
    }
    this.gravando = false;
    this.limparTimer();
  }

  descartarGravacao(): void {
    this.blobAudio = null;
    if (this.urlAudio) {
      URL.revokeObjectURL(this.urlAudio);
      this.urlAudio = null;
    }
    this.tempoGravacao = 0;
  }

  enviarGravacao(): void {
    if (!this.blobAudio) {
      return;
    }
    const extensao = this.blobAudio.type.startsWith('audio/mp4') ? 'm4a' : 'webm';
    const arquivo = new File([this.blobAudio], `gravacao.${extensao}`, {
      type: this.blobAudio.type || 'audio/webm',
    });
    this.enviarArquivo(arquivo);
  }

  enviarArquivo(arquivo: File | null): void {
    if (!arquivo) {
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
      .enviar(arquivo, this.titulo, (p) => (this.progressoUpload = p))
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

  private limparTimer(): void {
    if (this.timerGravacao !== null) {
      clearInterval(this.timerGravacao);
      this.timerGravacao = null;
    }
  }

  private pararStream(): void {
    this.streamAudio?.getTracks().forEach((track) => track.stop());
    this.streamAudio = null;
  }
}
