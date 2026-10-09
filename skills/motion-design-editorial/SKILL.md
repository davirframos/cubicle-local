---
name: motion-design-editorial
description: Gera overlays de motion graphics (Callout, Recorte, Ritmo, Mapa de Território, Janela de Footage) para o canal dark, usando HyperFrames/GSAP. Use quando o Editor precisar criar um desses 5 padrões visuais a partir do Manual Visual de Motion Design Editorial.
---

# Motion Design Editorial — padrões validados

Documenta 5 padrões de overlay de motion graphics do "Manual Visual de
Motion Design Editorial" (deck do canal dark), já validados ponta-a-ponta
no pipeline HyperFrames (init → build → check → snapshot → render → MP4).
Cada padrão tem um arquivo de referência com spec completa, timings,
técnica GSAP usada e os bugs reais encontrados (e como evitá-los).

Isto é conhecimento reutilizável, não código de produção: não está
plugado no `editor.py`/pipeline Paperclip ainda (esse FFmpeg script vive
fora deste repo, direto no servidor). Esta skill serve pra Claude Code
(Tech Lead) gerar rapidamente a composição HyperFrames de um desses
padrões quando o Editor pedir, sem repetir a investigação/depuração já
feita.

## Os 5 padrões

| Padrão | Duração | Uso típico | Referência |
| --- | --- | --- | --- |
| **Callout** | 4.00s | Destaque de frase/citação curta sobre fundo escuro | `references/callout.md` |
| **Recorte** | ver spec | "Cutout" de uma figura/forma com push-in de câmera | `references/recorte.md` |
| **Ritmo** | 7.60s | Sequência de corte seco com punch-ins (ritmo editorial) | `references/ritmo.md` |
| **Mapa de Território** | 4.25s | Mapa histórico com territórios aparecendo + timeline de anos | `references/territorio.md` |
| **Janela de Footage** | 6.25s | Janela de vídeo "flutuando" sobre um mapa/fundo, com morph pra selo circular | `references/janela.md` |

## Como usar

1. Leia o arquivo de referência do padrão pedido em `references/` — tem a
   spec visual (paleta, timings, beats) e o código GSAP já testado.
2. Rode o pipeline HyperFrames padrão nesse diretório de projeto:
   ```bash
   npx hyperframes init <dir> --non-interactive --example=blank --skill=motion-graphics
   npx hyperframes check .
   npx hyperframes snapshot --at <tempos-chave>
   npx hyperframes render . --skill=motion-graphics -q high -o ./renders/video.mp4
   ```
3. Antes de rodar `check`/`render`, confira `references/ambiente.md` —
   lista os workarounds de ambiente (CDN bloqueado, download de browser
   bloqueado) necessários pra rodar nesta infraestrutura.
4. Confira `references/gotchas-gsap.md` antes de escrever timelines GSAP
   novas — lista os 3 bugs reais (não hipotéticos) encontrados ao validar
   estes padrões, com a causa raiz e o fix.

## Estrutura de uma composição (convenção usada nos 5 padrões)

Todos os padrões seguem o padrão de sub-composição do HyperFrames:
- `index.html`: host fino, registra uma timeline raiz quase vazia em
  `window.__timelines["<id>-root"]`, com um `<div data-composition-src="compositions/scene.html">`.
- `compositions/scene.html`: a cena real, dentro de um `<template>` —
  CSS, markup e o `<script>` que monta a `gsap.timeline({paused:true})`
  real e registra em `window.__timelines["<id>"]`. O `data-composition-id`
  do host e do sub-comp têm que casar.

Paleta base do manual: fundo `#1F2224`, amarelo de destaque `#D8DA3A`
(callout) / `#CD3647` (vermelho de ênfase em outros padrões), texto claro
`#F4F2EC`. Fontes: serifa bold para frases de destaque, sans condensada
para rótulos/legendas, `'Courier New', monospace` para timestamps/HUD.
