# Padrão: Transição

Cena de passagem entre dois padrões de conteúdo (ex: Mapa de Território
→ Janela de Footage), quando o roteiro muda de assunto e precisa de um
respiro visual antes do próximo corte. Não vem do manual (não existe
slide `transicao.html` nos 58 arquivos do artifact) — foi inventada na
montagem do vídeo-teste "13 colônias, um império" (IAS-42) pra cobrir o
trecho de narração entre Território e Janela.

## Status

Validada uma vez, só nesse contexto (reaproveita a linguagem visual do
Callout — fundo escuro, amarelo neon, serifa — pra não destoar do resto
do vídeo). **Não tem a mesma garantia das outras 6 peças**: sem slide
do manual pra conferir contra, sem código-fonte versionado aqui no repo
(o projeto `videos/final-teste/transicao/` só existe no host do
Paperclip, não foi puxado pro GitHub). Se for usar esse padrão de novo,
vale pedir pro agente commitar o `compositions/scene.html` dele no
próximo uso, pra virar referência de verdade como as outras.

## Spec visual (observada no deliverable aprovado)

- Timeline: ~12s (ajustável à narração — essa duração foi escolhida
  pra cobrir a pausa de fala entre dois blocos de conteúdo).
- Fundo `#1F2224` (mesmo do Callout). Pequeno rótulo em caps/mono
  acima do texto (ex: "SÉCULO XX") em amarelo `#D8DA3A`.
- Texto principal centralizado, serifa, 2-3 linhas, revelado por
  fade/kinetic type leve (sem o trim-path de linha do Callout — mais
  estático).
- Traço horizontal amarelo fino na base, mesma linguagem do Callout.

## Quando usar

Só quando o roteiro muda de assunto/tom entre dois padrões visuais
fortes e precisa de uma pausa — não é pra virar o 6º padrão "oficial"
do manual. Prefira cortar direto entre os padrões quando o roteiro
permitir; a Transição existe pra cobrir os casos em que não dá.
