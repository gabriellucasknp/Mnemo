import { Component, OnInit } from '@angular/core';
import { RouterLink } from '@angular/router';

import { AulasService } from '../../core/aulas.service';
import { MlService } from '../../core/ml.service';
import { SimuladosService } from '../../core/simulados.service';
import { formatarData, minutosDuracao, tempoDecorrido } from '../../core/format';
import { Aula, Health, HealthDb, MlQuestoesStatus, MlStatus, Simulado } from '../../core/models';
import { IconComponent } from '../../shared/icon/icon.component';

interface StatCard {
  valor: string | number;
  rotulo: string;
}

@Component({
  selector: 'app-dashboard',
  imports: [RouterLink, IconComponent],
  templateUrl: './dashboard.html',
  styleUrl: './dashboard.scss',
})
export class DashboardComponent implements OnInit {
  aulas: Aula[] = [];
  simulados: Simulado[] = [];
  saudacao = 'Bom dia';
  stats: StatCard[] = [];

  apiOk = false;
  dbOk = false;
  mlStatus: MlStatus | null = null;
  mlQuestoesStatus: MlQuestoesStatus | null = null;

  erro: string | null = null;
  carregando = true;

  protected readonly formatarData = formatarData;
  protected readonly minutosDuracao = minutosDuracao;
  protected readonly tempoDecorrido = tempoDecorrido;

  constructor(
    private readonly aulasService: AulasService,
    private readonly simuladosService: SimuladosService,
    private readonly mlService: MlService,
  ) {}

  ngOnInit(): void {
    const hora = new Date().getHours();
    if (hora < 12) {
      this.saudacao = 'Bom dia';
    } else if (hora < 18) {
      this.saudacao = 'Boa tarde';
    } else {
      this.saudacao = 'Boa noite';
    }

    this.carregarDados();
    this.carregarStatus();
  }

  private carregarDados(): void {
    this.aulasService.listar().subscribe({
      next: (aulas) => {
        this.aulas = aulas;
        this.atualizarStats();
        this.carregando = false;
      },
      error: (err) => {
        this.erro = err.message;
        this.carregando = false;
      },
    });

    this.simuladosService.listar().subscribe({
      next: (simulados) => {
        this.simulados = simulados;
        this.atualizarStats();
      },
      error: () => undefined,
    });
  }

  private carregarStatus(): void {
    this.aulasService.health().subscribe({
      next: () => (this.apiOk = true),
      error: () => (this.apiOk = false),
    });

    this.aulasService.healthDb().subscribe({
      next: (health) => (this.dbOk = health.database === 'ok'),
      error: () => (this.dbOk = false),
    });

    this.mlService.statusFlashcards().subscribe({
      next: (status) => (this.mlStatus = status),
      error: () => undefined,
    });

    this.mlService.statusQuestoes().subscribe({
      next: (status) => (this.mlQuestoesStatus = status),
      error: () => undefined,
    });
  }

  private atualizarStats(): void {
    const totalMinutos = this.aulas.reduce(
      (acc, a) => acc + minutosDuracao(a.duracao_segundos),
      0,
    );
    this.stats = [
      { valor: this.aulas.length, rotulo: 'Aulas gravadas' },
      { valor: this.simulados.length, rotulo: 'Simulados criados' },
      { valor: totalMinutos, rotulo: 'Minutos de aula' },
    ];
  }
}
