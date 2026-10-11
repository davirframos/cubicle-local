# Achados: o que o HyperFrames já entrega pronto

Levantado em 2026-10-11 a partir de 8 vídeos-tutorial sobre HyperFrames
(~1h50 no total) + verificação direta no CLI. **O que está marcado
"verificado" foi confirmado rodando o comando aqui; o resto veio de OCR
dos frames dos vídeos e é indício, não fato.**

## Resumo em uma linha

Construímos do zero (manual Vox → 5 padrões → protótipos) uma boa parte
do que o HyperFrames já entrega pronto para exatamente o caso de
"packaging de vídeo falado". Antes de montar qualquer padrão novo,
checar se já existe.

## 1. Workflows oficiais que não estávamos usando (verificado)

Instalam sob demanda com `npx hyperframes skills update <nome>`:

- **`talking-head-recut`** — empacota um vídeo falado (entrevista,
  podcast) com cards gráficos temporizados: títulos, lower-thirds,
  callouts de dado, citações, side panels, picture-in-picture. O clipe
  roda intacto por baixo. Canvas 16:9 / 9:16 / 4:5. É literalmente o
  nosso caso de uso de cortes.
- **`embedded-captions`** — legendas sobre vídeo falado, com catálogo de
  **35 identidades** visuais. Roda local de ponta a ponta (transcrição
  + matting do sujeito).

Outros do mesmo conjunto (28 skills em `heygen-com/hyperframes`), não
instalados: `faceless-explainer`, `general-video`, `music-to-video`,
`product-launch-video`, `slideshow`, `pr-to-video`, `figma`,
`remotion-to-hyperframes`, mais efeitos (`glass-shard-title`,
`cuboid-carousel`, `orbit-card`, etc.).

### O que o `talking-head-recut` traz de infra

- Fontes `.woff2` e `gsap.min.js` **empacotados na própria skill**
  (`assets/fonts/`, `assets/vendor/`) — resolve sozinho os dois
  problemas que documentamos em `ambiente.md` (CDN do GSAP bloqueado,
  fontes ausentes).
- Transcrição local via `hyperframes transcribe` (Whisper), sem key.
- Referências prontas em `references/`: `frames/` (clean, hairline,
  polaroid), `layouts/` (overlay, pip, split), `styles/`,
  `DESIGN_INDEX.md`.
- Pipeline de arquivos: `metadata.json` → `audio.mp3` →
  `transcript.json` (array plano de palavras com `start`/`end`) →
  `storyboard.json` → `public/cards/card-XX.html` → `public/index.html`
  → `output.mp4`.
- 5 valores de `zone` por card (fullscreen, lower-third, side-panel,
  video-overlay, …) e matriz `Style × Layout × VideoFrame`.

## 2. Catálogo de legendas animadas (verificado)

`npx hyperframes catalog --tag caption-style` → 16 blocos prontos.
Os que interessam pra corte de podcast:

| Bloco | O que faz |
| --- | --- |
| `caption-highlight` | Varredura de fundo vermelho atrás da palavra ativa, estilo TikTok |
| `caption-pill-karaoke` | Container em pílula, highlight karaokê por palavra |
| `caption-kinetic-slam` | Palavra única em tela cheia, entrada alternando direção |
| `caption-editorial-emphasis` | Dois pesos/tamanhos de fonte, contraste dramático na palavra-chave |
| `caption-clip-wipe` | Wipe por `clip-path` da esquerda pra direita, por palavra |
| `caption-weight-shift` | Transição elegante de peso da fonte entre linhas |

Outros: `caption-camera-follow`, `caption-emoji-pop`,
`caption-glitch-rgb`, `caption-gradient-fill`, `caption-matrix-decode`,
`caption-neon-accent`, `caption-neon-glow`, `caption-parallax-layers`,
`caption-particle-burst`, `caption-texture`.

### As 35 identidades do `embedded-captions`

As relevantes pra corte de podcast: `anchor` (default — toda palavra
precisa ser lida), `documentary` (entrevistas, jornalismo — "gravidade é
o estilo"), `loud` (hype, reels sociais), `stomp` (hooks, aberturas — "as
palavras SÃO o show"), `keynote`.

## 3. Overlays sociais prontos (verificado)

`npx hyperframes catalog --tag social` → 13 blocos:

- `yt-comment-card` — comentários digitando sobre o footage (avatar,
  usuário, hora, caractere por caractere). Muito usado em corte viral.
- `yt-lower-third` — lower third de inscrever-se com avatar e canal.
- `tiktok-follow` / `instagram-follow` — overlay de seguir.
- `freeze-frame-dressing` — freeze-frame com papel, fita e flash.
- `editorial-flash-overlay` — corte com flash de câmera.
- `x-post`, `reddit-post`, `spotify-card`, `macos-notification`,
  `thread-message-stack` — cards de contexto.

Total: 43 blocos com tag `overlay`, 17 com `captions`, 17 com `text`.

## 4. Técnica de layout vista nos vídeos (indício, de OCR/frames)

O padrão que mais apareceu nos reels em português:

> "O vídeo deve se recolher para um retângulo vertical 9:16 com cantos
> arredondados, posicionado no canto inferior direito. A área central da
> tela deve se abrir para receber motion graphics e animações."

Ou seja: locutor começa full-bleed → recolhe pra PiP num canto → centro
abre pra cards. Nos frames finais dava pra ver legenda com
**palavra-chave em cor de destaque** no meio da frase (não a frase
inteira colorida).

**Safe zone de vertical** citada: ~380–450px livres na base (legendas,
botões de like/comentário/share/save, atribuição de áudio).

## 5. Confirmações do que já fazíamos certo

- "Keep GSAP local, every time, in every composition, never load it from
  CDN" — é o que o `ambiente.md` já manda.
- "HyperFrames renderiza deterministicamente e faz seek frame a frame,
  então o original não rodava como estava; reescrevi como camada
  seek-driven" — mesma regra do `janela.md` (nunca mutar DOM via
  `onUpdate`).
- Extrair frames do vídeo-fonte e revisar visualmente antes de montar —
  é o fluxo que adotamos a partir do IAS-40.

## 6. Números de referência

- Render de um reel: ~9 min (relatado em um dos vídeos).
- Transcrição Whisper: roda em background shell enquanto o resto segue.
- Custo: HyperFrames é grátis e renderiza local; o custo real são tokens.

## 7. Bloqueio conhecido deste ambiente

`hyperframes transcribe` e `hyperframes models install parakeet` baixam
os modelos de `huggingface.co`, **bloqueado por política de organização**
no sandbox do Claude (erro: `CONNECT tunnel failed, 403`). GitHub e
objects.githubusercontent.com passam; HF, `openaipublic.azureedge.net` e
`alphacephei.com` não. Consequência: a transcrição precisa rodar no host
do Paperclip (rede própria) ou na máquina do usuário, não aqui.

## 8. O manual Vox tem 12 padrões, não 5

`documentacao_motion_design_vox.md` descreve 12. Implementamos 5
(Callout, Recorte, Ritmo, Território, Janela). Não implementados: setas
pulsantes, photo-table com câmera 3D, gráfico sobre mapa, diagrama
técnico, **quote card sobre papel granulado**, film gate, outro burst.
O quote card é o único claramente útil pra corte de podcast.
