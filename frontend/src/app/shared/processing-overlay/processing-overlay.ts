import { Component, Input } from '@angular/core';

@Component({
  selector: 'app-processing-overlay',
  imports: [],
  templateUrl: './processing-overlay.html',
  styleUrl: './processing-overlay.scss',
})
export class ProcessingOverlayComponent {
  @Input() titulo = 'Processando...';
  @Input() passos: string[] = [];
  @Input() progresso = 0;
  @Input() mostrarBarra = false;
}
