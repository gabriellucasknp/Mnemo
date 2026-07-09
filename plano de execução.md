Etapa 1 — Esqueleto vivo no Docker
Por quê: antes de qualquer IA, você precisa de um corpo onde as peças conversam. A ideia central é a fatia vertical: um esqueleto que já roda de ponta a ponta fazendo o mínimo, pra você nunca estar num estado quebrado. Docker desde o dia 1 (decisão que você já tomou) garante que "funciona na minha máquina" vai ser igual a "funciona na AWS" lá na frente.
O que fazer: montar a estrutura de pastas e um docker-compose com dois serviços — a API (FastAPI) e o banco (Postgres). Subir uma rota trivial (tipo um /health que responde "ok"). Não precisa fazer nada útil ainda. Docker é seu, então isso é montagem; o único conceito novo aqui é o FastAPI como servidor — como ele sobe e atende uma rota.
Checkpoint: você roda o docker compose up, abre o navegador num endereço local e vê o "ok". Depois abre o /docs (o FastAPI gera uma interface automática) e a tela dele aparece. Se isso acontece, o corpo está vivo.


Etapa 2 — Whisper em isolamento
Por quê: o Whisper é a peça mais nova e a de maior risco. Regra de ouro de projeto de ML: prove a peça incerta sozinha, antes de embrulhar ela em web + banco + Docker. Se você junta tudo de cara e dá erro, você não sabe quem errou. Isolado, o erro só pode vir de um lugar.
O que fazer: um script Python solto que recebe o caminho de um áudio de teste e imprime a transcrição. Grave uns 30 segundos de você falando pra usar de cobaia. Aqui você aprende: o que é "carregar um modelo", a diferença entre os tamanhos (tiny/base/small...) e o trade-off velocidade × qualidade, e que a primeira execução baixa o modelo.
Checkpoint: você roda o script com seu áudio e o texto da sua fala aparece no terminal. E você consegue explicar, com suas palavras, por que escolheu o tamanho de modelo que escolheu.


Etapa 3 — Conectar o Whisper ao fluxo web
Por quê: agora você junta a peça nova (etapa 2) ao corpo (etapa 1). Conceito central: upload de arquivo via HTTP — como um áudio sai do seu computador, sobe pela rede e chega no Python. É a primeira vez que dado de verdade atravessa o sistema inteiro.
O que fazer: uma rota no FastAPI que recebe o upload do áudio, salva temporariamente, chama a função do Whisper da etapa 2 e devolve a transcrição como resposta. Teste tudo pelo /docs — você ainda não precisa de tela nenhuma. Você vai esbarrar num incômodo: o Whisper demora, então a requisição fica "pensando" um tempão. Está tudo bem — anota mentalmente "é isso que o Celery vai resolver na fase futura" e segue. Não resolve agora.
Checkpoint: pelo /docs, você sobe um arquivo de áudio e recebe a transcrição de volta no navegador. O áudio atravessou o sistema.


Etapa 4 — Persistir: o banco e a regra da fonte
Por quê: até aqui a transcrição evapora quando a requisição termina. Agora ela vira memória permanente — o propósito do produto. E entra a decisão de design mais importante que você tomou: a transcrição é a fonte de verdade. Você vai modelar isso no banco explicitamente desde já, mesmo que no MVP só exista uma fonte. O conceito é origem do dado (provenance) — marcar de onde cada informação veio. Isso prepara o terreno pro complemento da IA das fases futuras sem você ter que refazer o banco depois.
O que fazer: o desenho das tabelas é território seu (SQL). O novo é conectar o Python ao Postgres — vou te ajudar a decidir entre um driver direto e um ORM quando chegarmos. Modele pelo menos uma tabela de "aula/sessão" e uma de "transcrição", com um campo que marca a origem do texto. Faça a rota da etapa 3 salvar em vez de só devolver.
Checkpoint: você sobe um áudio, fecha tudo, reabre, e consulta o banco com SQL puro — a transcrição está lá, com a origem marcada. A memória persiste entre dias. (Esse é o ponto onde o Mnemo cumpre sua razão de existir.)


Etapa 5 — Geração de flashcards com IA
Por quê: esta é a saída-núcleo, a razão do MVP existir. Conceito central de ML aplicado: você vai pedir a um modelo de linguagem pra transformar texto corrido (a transcrição) em pares pergunta-resposta estruturados. Dois sub-conceitos que valem ouro: (a) como você pede (o prompt) molda o que sai; (b) a saída precisa vir num formato que seu código consiga ler de volta — estruturado, não um texto solto.
O que fazer: uma função que pega uma transcrição salva, manda pro modelo com instruções pra gerar flashcards, recebe os pares P/R e os salva numa tabela de flashcards — ligada à aula de origem e com a origem marcada (mesma regra da etapa 4: estes vêm da fala do professor). Aqui você decide modelo local × via API — te ajudo a pesar quando chegar.
Checkpoint: a partir de uma transcrição no banco, o sistema gera e salva flashcards. Você abre o banco e vê perguntas e respostas que fazem sentido em relação ao áudio que gravou.

Etapa 6 — A tela: ver e estudar
Por quê: até agora você testou tudo pelo /docs. Agora o produto ganha rosto. Conceito: renderização no servidor — o Python monta o HTML já preenchido com seus dados e manda pro navegador (Jinja2), sem framework JS pesado, como a gente combinou. E aqui você materializa visualmente a regra da fonte: transcrição numa seção, flashcards em outra — deixando claro o que é "dito" e, no futuro, o que é "complemento da IA".
O que fazer: duas telas simples — uma pra subir o áudio, outra pra ver os flashcards de uma aula. HTML + CSS seus, preenchidos pelo FastAPI via Jinja2. Não precisa ser bonito; precisa ser claro e separar as seções.
Checkpoint: do navegador, sem tocar no /docs, você sobe um áudio, espera, e vê seus flashcards numa página. Nesse momento o MVP do Mnemo está vivo e completo. É um produto que você pode mostrar.

E o que ficou parado de propósito, esperando virar fase depois do MVP: quiz (a engine já existe, é só reembalar), busca semântica (pgvector), fila (Celery+Redis, pra matar aquele congelamento da etapa 3), e deploy na AWS. Cada um é uma fase, cada fase adiciona uma coisa, na ordem.
Repara num detalhe: as etapas 1 a 4 são quase todas território que você já domina, com só um conceito novo cada. O "novo de verdade" se concentra nas etapas 2 e 5. O resto é você construindo sobre chão firme.
Antes de eu te soltar na Etapa 1: o nível de detalhe das etapas tá bom pra você, ou você quer que eu quebre alguma delas em passos ainda menores? E, se já tiver fechado, é só dizer que eu te acompanho na primeira.


