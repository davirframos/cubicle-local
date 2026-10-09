# Padrão: Ritmo

Sequência de corte editorial: plano aberto → 3 punch-ins rápidos em
sequência → close estático com seta de anotação cutucando em loop →
corte seco pra preto. Usado pra dar "ritmo" de edição dentro de um
único clipe de overlay.

## Spec visual

- Timeline: **7.60s**.
- Fundo `#1f2224`. Duas "silhuetas" placeholder (`#shotA` cor
  `#c9a98c`, `#shotB` cor `#8c9ac9`) representando dois sujeitos/planos.
- Seta de anotação vermelha (`#cd3647`) aponta durante o close.
- `#camera` é o wrapper que toda a câmera (cortes/punch-ins) escala —
  `transform-origin: 0 0` fixo no wrapper, a origem real de cada corte é
  controlada por `transformOrigin` dinâmico por tween (ver técnica).

## Beats

| Tempo | Beat |
| --- | --- |
| 0.00–4.00s | Plano aberto: câmera parada, `frame(540, 960, 1)` (centro do canvas, sem zoom) |
| 4.00–4.30s | Corte 1: aproxima de A, `frame(370, 910, 1.8)` |
| 4.30–4.60s | Corte 2: ainda mais perto de A, `frame(370, 880, 2.2)` |
| 4.60–4.90s | Corte 3 (com leve panorâmica): desliza de A pra B, tween de 0.2s até `frame(780, 950, 2.2)` |
| 4.90–7.40s | Close estático em B: `frame(780, 940, 2.6)`, seta aparece (0.15s) e cutuca em loop (`yoyo`, `repeat:4`, 0.5s cada ciclo) |
| 7.40–7.60s | Saída: corte seco pra preto, `#cutveil opacity: 0→1`, ease `none`, 0.2s |

## Técnica de câmera: punch-in via `transformOrigin` pinning

Esta é a técnica correta pra fazer a câmera "entrar" num ponto de
conteúdo `(cx, cy)` com um `scale` dado, deixando esse ponto centralizado
na tela. Tentativas anteriores calculando `x`/`y` manualmente (ex:
`x = 540 - cx*scale`) deram resultado errado (conteúdo quase todo fora
da tela). Ver `gotchas-gsap.md` #2 para a explicação completa do bug.

```js
// Fixa transformOrigin no ponto de conteúdo que queremos centralizar
// sob o zoom, depois usa x/y (offset plano em pixel, sempre ignorando
// scale/origin) pra levar esse ponto (agora fixo) até o centro do
// canvas (540, 960 — canvas 1080x1920).
function frame(cx, cy, scale) {
  return { transformOrigin: `${cx}px ${cy}px`, scale, x: 540 - cx, y: 960 - cy };
}
```

## Código de referência (testado, `check` passa)

```js
const tl = gsap.timeline({ paused: true });

tl.set("#camera", frame(540, 960, 1), 0);

tl.set("#camera", frame(370, 910, 1.8), 4.0);
tl.set("#camera", frame(370, 880, 2.2), 4.3);
tl.to("#camera", { ...frame(780, 950, 2.2), duration: 0.2, ease: "power1.inOut" }, 4.6);

tl.set("#camera", frame(780, 940, 2.6), 4.9);
tl.to("#arrow", { opacity: 1, duration: 0.15 }, 4.9);
tl.to("#arrow", { x: "+=5", y: "-=4", duration: 0.5, ease: "sine.inOut", yoyo: true, repeat: 4 }, 5.0);

tl.to("#cutveil", { opacity: 1, duration: 0.2, ease: "none" }, 7.4);
```

CSS chave: `#camera { position:absolute; inset:0; transform-origin: 0 0; }`
— o `transform-origin` estático no CSS é só um placeholder; cada `frame()`
sobrescreve via GSAP com o `transformOrigin` dinâmico correto.

`#cutveil` é um `div` `position:absolute; inset:0; background:#000; opacity:0;`
sobreposto a tudo, usado só pra saída em corte seco.
