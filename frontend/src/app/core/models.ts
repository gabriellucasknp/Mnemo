export type Origem = 'professor' | 'ia';

export type CategoriaFlashcard = 'conceito' | 'definição' | 'processo' | 'exemplo';

export interface Transcricao {
  id: number;
  texto: string;
  idioma: string | null;
  origem: Origem;
  criada_em: string;
}

export interface Flashcard {
  id: number;
  categoria: CategoriaFlashcard;
  pergunta: string;
  resposta: string;
  explicacao: string | null;
  origem: Origem;
}

export interface Aula {
  id: number;
  titulo: string;
  materia: string | null;
  duracao_segundos: number | null;
  criada_em: string;
  flashcards_count: number;
}

export interface AulaDetalhe extends Aula {
  transcricao: Transcricao | null;
  flashcards: Flashcard[];
}

export interface Questao {
  id: number;
  enunciado: string;
  alternativas: Record<string, string>;
  explicacao: string | null;
  dificuldade: string;
  disciplina: string | null;
}

export interface Simulado {
  id: number;
  titulo: string;
  materia: string | null;
  quantidade_questoes: number;
  dificuldade: string;
  aula_id: number | null;
  criado_em: string;
  questoes?: Questao[];
  total_acertadas: number;
  total_respondidas: number;
}

export interface RespostaResultado {
  questao_id: number;
  alternativa_marcada: string | null;
  gabarito: string;
  acertou: boolean;
  explicacao: string | null;
}

export interface ResultadoSimulado {
  simulado_id: number;
  total_questoes: number;
  acertadas: number;
  erros: number;
  percentual: number;
  detalhes: RespostaResultado[];
}

export interface Health {
  status: string;
  version: string;
  debug: boolean;
}

export interface HealthDb {
  status: string;
  database: string;
}

export interface ApiError {
  detail: string;
}
