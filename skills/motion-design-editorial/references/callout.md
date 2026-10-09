# Padrão: Callout

Destaque de frase/citação curta sobre fundo escuro. Primeiro padrão
validado no pipeline — serviu pra confirmar init → check → snapshot →
render de ponta a ponta.

## Spec visual

- Timeline: **4.00s**, vertical 1080x1920.
- Paleta: fundo `#1F2224`, amarelo neon `#D8DA3A`, texto `#F4F2EC`.
- Fonte: serifa bold pra frase principal, sans condensada pro rótulo/sigla.

## Beats

| Tempo | Beat |
| --- | --- |
| 0.00–0.25s | Linha: traço amarelo neon, diagonal→horizontal, trim path 0→100%, ease-out |
| 0.25–0.50s | Rótulo: sigla curta bold, "pop" de escala |
| 0.50–1.00s | Frase: texto serifa bold, máscara vertical de baixo pra cima |
| 0.60–0.80s | Destaque: marcador amarelo atrás de parte do texto, `scaleX` 0→1 |
| 1.00–3.50s | Permanência: tudo parado |
| 3.50–3.75s | Saída: tudo sai em até 0.25s |

## Estrutura HyperFrames

Sub-composição padrão: `index.html` (host, `data-duration="4"`,
registra timeline raiz vazia) + `compositions/scene.html` (cena real,
dentro de `<template>`).

## Bugs/avisos encontrados

- `negative_z_index`: a implementação inicial pôs o marcador de
  destaque (`.hl-bg`) atrás do texto via `z-index:-1`. Lint reprova.
  **Fix:** remover o `z-index` e confiar na ordem do DOM (div do
  marcador antes da div do texto no HTML = marcador pinta primeiro,
  fica atrás visualmente).
- `nested_structure_needs_subcomposition`: markup inicial era aninhado
  demais num único arquivo; foi reestruturado pro padrão host +
  sub-composição.
- Aviso de contraste no texto destacado: por ~0.1s o texto escuro fica
  sobre fundo escuro antes do marcador amarelo animar embaixo dele —
  é um warning (não error), autorresolve em menos de 0.1s, aceitável.
- Workarounds de ambiente (CDN do GSAP bloqueado, download do
  headless shell bloqueado) — ver `ambiente.md`.

## Como reconstruir

1. `npx hyperframes init <dir> --non-interactive --example=blank --skill=motion-graphics`
2. `npm install gsap@3.14.2 --no-save` (ver `ambiente.md`)
3. Montar `index.html` (host) e `compositions/scene.html` (cena) seguindo
   os beats acima — linha com `clip-path`/trim-path animado por GSAP,
   rótulo com `scale` pop, frase com máscara (`clip-path: inset(100% 0 0 0)` → `inset(0 0 0 0)`), marcador com `scaleX` 0→1.
4. `npx hyperframes check .` — confirme 0 erros.
5. `npx hyperframes snapshot --at 0,0.25,0.5,0.7,1,3.6,3.9` (tempos
   cobrindo cada beat) pra revisão visual.
6. `npx hyperframes render . --skill=motion-graphics -q high -o ./renders/video.mp4`
