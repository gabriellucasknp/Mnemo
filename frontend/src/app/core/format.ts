export function formatarData(iso: string | null | undefined): string {
  if (!iso) {
    return '';
  }
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) {
    return '';
  }
  return data.toLocaleDateString('pt-BR');
}

export function minutosDuracao(segundos: number | null | undefined): number {
  if (!segundos || segundos <= 0) {
    return 0;
  }
  return Math.max(1, Math.floor(segundos / 60));
}

export function tempoDecorrido(iso: string | null | undefined): string {
  if (!iso) {
    return '';
  }
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) {
    return '';
  }
  const seg = Math.max(0, Math.floor((Date.now() - data.getTime()) / 1000));
  if (seg < 60) {
    return 'agora mesmo';
  }
  const min = Math.floor(seg / 60);
  if (min < 60) {
    return `há ${min} min`;
  }
  const horas = Math.floor(min / 60);
  if (horas < 24) {
    return `há ${horas} h`;
  }
  const dias = Math.floor(horas / 24);
  if (dias < 30) {
    return `há ${dias} d`;
  }
  return formatarData(iso);
}
