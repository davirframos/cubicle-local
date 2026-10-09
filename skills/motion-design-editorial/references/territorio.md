# Padrão: Mapa de Território

Mapa histórico (ex: expansão territorial dos EUA) com zoom-out de
câmera, territórios aparecendo um a um sincronizados com rótulo de
evento + marcador numa barra de linha do tempo (anos).

## Spec visual

- Timeline: **4.25s**.
- Fundo `#dad9d1`. Mapa num card claro (`#f4f2ec`) com territórios
  (`.territory`, azul `#5a7896`→`#0058a8` quando "ativo") e uma tag
  (`.tag`, cinza `#8a8a84`).
- HUD (rótulo de evento + timeline de anos) fica **fora** do `#camera`
  — não escala com o zoom, é overlay fixo.
- Timeline de anos mapeada de 1776 a 2017 numa barra de 760px.

## Beats

| Tempo | Beat |
| --- | --- |
| 0.00–3.00s | Câmera: zoom-out, `#camera scale: 1.35 → 1`, ease `power1.inOut` |
| 0.10s | 1783 — "Estados e territórios" aparece (território `#t1`), rótulo troca, marcador vai pra 1783 |
| 0.70s | 1803 — Louisiana Purchase (`#t2`) |
| 1.35s | 1819 — Flórida, só uma *tag* cinza (`#t3`), não território cheio |
| 1.90s | 1845 — Texas Annexation (`#t4`) |
| 2.55s | 1846 — Oregon Country (`#t5`) |
| 3.15s | 1848 — Mexican Cession (`#t6`) |
| 3.48–4.00s | Permanência: mapa completo parado |
| 4.00–4.25s | Saída: `#root opacity: 1→0`, ease `power2.in`, 0.25s |

Cada território usa o helper `territoryIn(id, time)`: fade+cor de
`opacity:0.4 / #5a7896` pra `opacity:1 / #0058a8` em 0.33s. A tag usa
`tagIn(id, time)`: só fade de opacidade. O rótulo usa `labelSwap(id, time, duration)`:
fade-in então fade-out depois de `duration`. O marcador usa
`markerTo(year, time)`: tween de `x` até a posição X calculada do ano.

## Bug real: `immediateRender` do `fromTo()` (ver `gotchas-gsap.md` #3)

Todos os 6 territórios apareciam a ~40% de opacidade desde o frame 0,
antes de qualquer evento programado — mesmo passando
`immediateRender:false` no `fromTo()` individual (não resolveu).

**Fix:** declarar explicitamente o estado em `t=0` com `tl.set(...)`
antes de qualquer `fromTo()` agendado:

```js
tl.set("#t1, #t2, #t3, #t4, #t5, #t6", { opacity: 0, backgroundColor: "#5a7896" }, 0);
```

## Outros fixes de lint aplicados

- `gsap_css_transform_conflict`: `#marker` tinha `transform: translateX(-14px)`
  estático no CSS conflitando com tween GSAP de `x`. **Fix:** removido
  o CSS, substituído por `tl.set("#marker", {x:-14}, 0)` como estado
  inicial declarado via GSAP.
- `font_family_without_font_face`: `'Archivo Narrow'` e `'JetBrains Mono'`
  do manual original não tinham `@font-face` no ambiente de render.
  **Fix:** `Arial, Helvetica, sans-serif` e `'Courier New', monospace`.

## Código de referência (testado, `check` passa)

```js
const tl = gsap.timeline({ paused: true });
const yearX = (y) => ((y - 1776) / (2017 - 1776)) * 760;

tl.fromTo("#camera", { scale: 1.35 }, { scale: 1, duration: 3, ease: "power1.inOut" }, 0);

// baseline explícito — evita o bug de immediateRender
tl.set("#t1, #t2, #t3, #t4, #t5, #t6", { opacity: 0, backgroundColor: "#5a7896" }, 0);

function territoryIn(id, time) {
  tl.fromTo(id, { opacity: 0.4, backgroundColor: "#5a7896" },
    { opacity: 1, backgroundColor: "#0058a8", duration: 0.33, ease: "power1.out" }, time);
}
function tagIn(id, time) {
  tl.to(id, { opacity: 1, duration: 0.33, ease: "power1.out" }, time);
}
function labelSwap(id, time, duration) {
  tl.to(id, { opacity: 1, duration: 0.2 }, time);
  tl.to(id, { opacity: 0, duration: 0.2 }, time + duration);
}
// marker tem 28px de largura (ponta do triângulo a 14px de cada lado);
// -14 recentraliza a ponta na posição X calculada do ano.
tl.set("#marker", { x: -14 }, 0);
function markerTo(year, time) {
  tl.to("#marker", { x: yearX(year) - 14, duration: 0.33, ease: "power1.inOut" }, time);
}

territoryIn("#t1", 0.1);  labelSwap("#ev1", 0.1, 0.5);  markerTo(1783, 0.1);
territoryIn("#t2", 0.7);  labelSwap("#ev2", 0.7, 0.5);  markerTo(1803, 0.7);
tagIn("#t3", 1.35);       labelSwap("#ev3", 1.35, 0.4); markerTo(1819, 1.35);
territoryIn("#t4", 1.9);  labelSwap("#ev4", 1.9, 0.5);  markerTo(1845, 1.9);
territoryIn("#t5", 2.55); labelSwap("#ev5", 2.55, 0.5); markerTo(1846, 2.55);
territoryIn("#t6", 3.15); labelSwap("#ev6", 3.15, 0.5); markerTo(1848, 3.15);

tl.to("#root", { opacity: 0, duration: 0.25, ease: "power2.in" }, 4.0);
```
