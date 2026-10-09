# Padrão: Janela de Footage

Uma "janela" de vídeo (retângulo preto com footage) aparece sobre um
mapa, reage a um evento no mapa (ex: país muda de cor/some), some, e
depois um segundo momento faz a janela "morphar" num selo circular
(retrato). Barra de progresso no HUD acompanha o tempo total.

## Spec visual

- Timeline: **6.25s**.
- Fundo `#dad9d1`. Mapa placeholder (`#f4f2ec`) com uma forma de país
  (`#ussr`, vermelho `#cd3647`) e uma bússola (`#compass`) que só
  aparece depois que a janela some.
- Janela de footage: retângulo preto `#window` com `#footage` (gradiente
  placeholder) dentro e um ícone de play (`#play`).
- Legenda de evento (nome + timestamp) no canto inferior direito +
  barra de progresso (`#progress-track`/`#progress-fill`, vermelho `#cd3647`).

## Beats

| Tempo | Beat |
| --- | --- |
| 0.00–0.30s | Entrada: `#window` aparece (`opacity:0→1, scale:0.92→1`), ease `power2.out` |
| 0.50–0.80s | Footage faz fade-in dentro da janela (0.3s depois da janela), ícone de play aparece em 0.65s |
| 0.80–3.80s | Mapa reage: `#ussr` vai de vermelho opaco a laranja translúcido e some (`backgroundColor` + `opacity:1→0`, 3s, ease `power1.inOut`) |
| 3.80–4.10s | Saída: `#window` some (`opacity:1→0, scale:1→0.96`), bússola aparece (`#compass opacity:0→1`) |
| 4.10–5.40s | Permanência: mapa limpo, parado |
| 5.40–6.00s | Morph: `#window` vira selo circular — `width/height: →420px, borderRadius: →210px`, 0.6s, ease `power2.inOut` |
| 6.00–6.25s | Saída final: `#root opacity:1→0`, 0.25s, ease `power2.in` |
| 0.00–6.25s | Barra de progresso: `#progress-fill width: 0%→100%`, `duration:6.25`, ease `none`, acompanha o tempo total |

Legenda de evento troca de texto via `setEvent(name, time, at)` —
usa `tl.set(..., {textContent: ...}, at)` em `#evname`/`#evtime`.

## Nota de implementação: barra de progresso

A primeira ideia foi usar `tl.eventCallback("onUpdate", ...)` pra
mutar `#progress-fill.style.width` direto via `document.getElementById`.
Isso foi descartado **antes mesmo de rodar `check`** por ser menos
idiomático/determinístico numa timeline GSAP seekável — foi substituído
por um tween simples, que é seek-safe por natureza:

```js
tl.fromTo("#progress-fill", { width: "0%" }, { width: "100%", duration: 6.25, ease: "none" }, 0);
```

**Regra geral:** nunca mute DOM diretamente via `onUpdate`/callback
numa composição HyperFrames — sempre use um tween GSAP normal, mesmo
pra coisas "simples" como uma barra de progresso. Isso garante que
`seek()` em qualquer tempo arbitrário (usado por `snapshot`/`check`)
produza o estado visual correto.

## Status

Nenhum bug maior — `check` passou limpo na primeira tentativa real
(depois dos mesmos ajustes de fallback de fonte usados em Território:
`'Archivo Narrow'`→`Arial, Helvetica, sans-serif`, `'JetBrains Mono'`→`'Courier New', monospace`).

## Código de referência (testado, `check` passa)

```js
const tl = gsap.timeline({ paused: true });

function setEvent(name, time, at) {
  tl.set("#evname", { textContent: name }, at);
  tl.set("#evtime", { textContent: time }, at);
}

tl.fromTo("#window", { opacity: 0, scale: 0.92 }, { opacity: 1, scale: 1, duration: 0.3, ease: "power2.out" }, 0);
setEvent("ENTRADA", "6:51,75", 0);

tl.to("#footage", { opacity: 1, duration: 0.3, ease: "power1.out" }, 0.5);
tl.fromTo("#play", { opacity: 0 }, { opacity: 1, duration: 0.2 }, 0.65);

setEvent("MAPA REAGE", "6:52–6:55", 0.8);
tl.to("#ussr", { backgroundColor: "#e98a2e", opacity: 0, duration: 3, ease: "power1.inOut" }, 0.8);

setEvent("SAÍDA", "6:57", 3.8);
tl.to("#window", { opacity: 0, scale: 0.96, duration: 0.3, ease: "power2.in" }, 3.8);
tl.to("#compass", { opacity: 1, duration: 0.3, ease: "power1.out" }, 3.9);

setEvent("MORPH", "7:16", 5.4);
tl.set("#window", { opacity: 1, scale: 1, borderRadius: 18 }, 5.4);
tl.set("#play", { opacity: 0 }, 5.4);
tl.set("#footage", { opacity: 1 }, 5.4);
tl.to("#window", { width: 420, height: 420, borderRadius: 210, duration: 0.6, ease: "power2.inOut" }, 5.4);

tl.to("#root", { opacity: 0, duration: 0.25, ease: "power2.in" }, 6.0);

tl.fromTo("#progress-fill", { width: "0%" }, { width: "100%", duration: 6.25, ease: "none" }, 0);
```
