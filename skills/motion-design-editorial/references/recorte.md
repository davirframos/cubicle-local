# Padrão: Recorte

"Cutout": letra(s) gigante(s) vermelho chapado sobre papel claro, com
entrada seca por slide, câmera dando push-in e depois voltando pro
plano aberto, saída por slide vertical. Bate com o slide `cutout.html`
do manual (padrão Recorte).

## Histórico — v1 descartada

A primeira implementação (letra "OK" placeholder + silhuetas de
multidão + chão, câmera push-in/zoom-out num card 820×820) foi
validada tecnicamente (pipeline init→check→snapshot→render funcionando),
mas **rejeitada no visual** pelo usuário ("não achei tão bonito") e,
mais importante, **não batia com a spec real do manual** — foi
reconstruída do zero como v2 (abaixo). Não usar a v1 como referência;
ela ficou só documentada aqui por histórico até esta correção.

## Spec visual (v2 — validada e aprovada)

- Timeline: **~4s**, vertical 1080×1920.
- Paleta: fundo papel `#F1F1F1`, letra(s) vermelho chapado `#CD3647`,
  barras estilo "assinatura"/onda sonora no terço inferior em
  `#1F2224`/`#3A3A36` alternadas.
- Layout: letra/número monumental centralizado (ex: "13" em Arial 900,
  ~440px, `letter-spacing: -0.05em`), ocupando a maior parte do quadro.
  Sem silhuetas de multidão — a v1 tinha isso, a spec real do manual não.

## Beats

| Tempo | Beat |
| --- | --- |
| 0.0–0.4s | Entrada seca: a letra desliza da direita, as barras da esquerda, **sem fade** — só slide |
| 0.4–2.4s | Câmera: push-in, `#camera scale: 1.0 → 1.08`, ease `power1.inOut` |
| 2.4–3.5s | Câmera: zoom-out de volta, `scale: 1.08 → 1.0` |
| 3.5–3.8s | Saída: slide vertical do quadro inteiro, `#root yPercent: 0 → -100`, revela o fundo escuro do host (transição pra próxima faixa) |

## Verificação (feita no build validado)

Pixel-análise nos snapshots `--at 0.4,1.5,3.0,3.8` + nos mesmos tempos
extraídos do MP4 final (resultado idêntico):

- 0.4s: 93.5% do quadro é papel `#F1F1F1`; "13" vermelho centrado
  (bbox 436×328px), câmera ainda em scale 1.0 — chegada por slide, sem
  fade. Barras visíveis na base.
- 1.5s: bbox cresceu pra 456×344px (scale efetivo ≈1.046, bate com o
  progresso eased de 1.0→1.08 nesse tempo).
- 3.0s: bbox 452×338px (scale efetivo ≈1.03), voltando pro plano
  aberto.
- 3.8s: quadro 100% `#1F2224` (fundo escuro do host) — slide de saída
  completo em 0.3s, dentro da faixa de 0.25–0.5s do manual.

`npm run check`: 0 erros, 0 warnings (6 infos de `container_overflow`
esperados do zoom de câmera/saída, mesmo padrão dos outros protótipos).

## Nota de ambiente

Fallback de fonte: `Arial, Helvetica, sans-serif` pra letra (sem
`@font-face` disponível no ambiente de render — ver `ambiente.md`).
