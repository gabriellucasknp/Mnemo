Mini-SDD — Mnemo
1. Identidade
Nome: Mnemo (de Mnemósine, deusa grega da memória)

Tipo: Projeto pessoal de Data Science + Machine Learning, com fim de aprendizado e portfólio.
2. O que faz (em 2 frases)
Mnemo capta o áudio de uma aula presencial ao vivo, transcreve e gera flashcards pra estudo posterior. É uma rede de segurança pro conteúdo que a atenção deixou passar durante a aula.
3. Usuário e gatilho de uso
Usuário: uso pessoal (você; no máximo pessoas próximas). Sem multiusuário complexo.

Gatilho: o usuário entra numa aula presencial e abre o Mnemo no notebook/celular pra capturar enquanto o professor fala.
4. Entradas e saídas
Entrada: áudio de aula presencial, capturado ao vivo.

Saídas:

Transcrição (dado primário, fonte de verdade)
Flashcards pergunta-resposta (saída-núcleo do MVP)
Futuras: quiz, busca semântica, slides, dashboard

5. Regra de negócio crítica
A fala do professor é a fonte de verdade. Qualquer complemento gerado pela IA é secundário, exibido em seção separada e marcado como tal. Se o complemento da IA contradiz o professor, o professor sempre "vence" e a IA fica como aviso. (Isso vai virar separação explícita na modelagem do banco: origem do dado marcada.)
6. Stack validada (pela régua "quebra o MVP / propósito?")
MVP — agora:
PeçaPapelPor que agoraPythonlinguagem basevocê já sabe; língua do MLWhispertranscrição (áudio→texto)sem ele não há texto, logo não há flashcard — quebraFastAPIponte tela↔Pythonsem ela a tela não fala com o backend — quebraPostgreSQLpersistênciapropósito do produto é memória entre dias — quebra o propósitoDockerempacotamentocusto de adiar > custo de começar com ele
Fases futuras — depois:

pgvector (busca semântica) · Celery+Redis (fila pra não travar a tela) · geração de flashcards refinada · quiz (mesma engine reembalada) · AWS (ECS/RDS/S3)
7. Mapa de conhecimento (honesto)
Já domino: Python, SQL, Docker.

Vou aprender no projeto, uma peça por fase: chamar modelo de ML (Whisper), geração com IA, embeddings/busca, filas assíncronas, deploy AWS.

Maior desafio declarado: primeiro projeto de ML e primeira vez com AWS.
8. Princípio condutor do projeto
Ambição sequenciada, não podada. Cada fase encaixa uma coisa nova sobre a base que já existe. O objetivo não é o projeto com mais buzzwords — é o projeto terminado, cujas decisões você consegue defender.