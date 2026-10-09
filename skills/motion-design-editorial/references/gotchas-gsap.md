# Gotchas reais do GSAP encontrados nestes padrões

Três bugs de verdade (não hipotéticos) apareceram ao validar os 5
padrões. Todos têm a mesma raiz: GSAP tem comportamentos "espertos" que
quebram a determinismo esperado de uma timeline pausada e `seek()`-ável
(que é o contrato do HyperFrames). Leia isto antes de escrever uma
timeline nova.

## 1. Coordenadas locais vs. coordenadas do canvas inteiro (Recorte)

Elementos posicionados com `top`/`left` absolutos precisam ser filhos
(diretos ou indiretos) do container que estabelece o *containing block*
pretendido. No protótipo de Recorte, letra/multidão/chão estavam
posicionados relativos ao `#camera` (canvas 1080x1920 inteiro) quando
deveriam estar relativos ao `#card` (card local 820x820) — causou
desalinhamento severo durante o push-in de câmera.

**Fix:** sempre confirme qual elemento é o `position: relative/absolute`
pai pretendido antes de escrever `top`/`left` nos filhos. Se a intenção é
"dentro do card", o card tem que ser `position: absolute` (ou `relative`)
e os filhos devem usar coordenadas *locais* ao card, não ao canvas.

## 2. Matemática de punch-in de câmera (Ritmo)

Pra fazer a câmera "entrar" num ponto de conteúdo (cx, cy) com um dado
`scale` e deixar esse ponto centralizado na tela, a abordagem ingênua de
calcular `x`/`y` combinando manualmente escala e origem (ex:
`x = 540 - cx*scale` ou `x = 540/scale - cx`) é fácil de errar — o
GSAP compõe `transformOrigin` + `scale` + `x`/`y` numa ordem que não é
intuitiva de deduzir de cabeça.

**Fix (abordagem que funciona de forma confiável):** fixar o
`transformOrigin` exatamente no ponto de conteúdo que você quer
congelar sob o zoom, e usar `x`/`y` como um offset de pixel *plano* —
que o GSAP sempre aplica sem ser afetado por `scale`/`transformOrigin` —
pra mover esse ponto (já fixo) até o centro do canvas:

```js
function frame(cx, cy, scale) {
  return {
    transformOrigin: `${cx}px ${cy}px`,
    scale,
    x: 540 - cx,   // 540 = centro horizontal do canvas 1080px
    y: 960 - cy,   // 960 = centro vertical do canvas 1920px
  };
}
tl.set("#camera", frame(370, 910, 1.8), 4.0);
```

Isso funciona porque `transformOrigin` tem semântica CSS bem definida
(o ponto de origem nunca se move sob escala) e `x`/`y` do GSAP são
documentadamente um offset plano em pixels, independente de
escala/origem.

## 3. `fromTo()` com `immediateRender` (Território)

Por padrão, `gsap.fromTo()` tem `immediateRender: true` — ou seja, os
valores "from" são aplicados **imediatamente na criação do tween**,
mesmo que o tween esteja agendado mais pra frente na timeline. Isso
causa elementos aparecendo (ex: com opacidade parcial) desde o frame 0,
antes do evento programado.

No protótipo de Território, 6 formas de território apareciam a ~40% de
opacidade desde o início, antes de qualquer evento — mesmo com
`immediateRender: false` passado no `fromTo()` individualmente, o bug
persistia (comportamento inesperado/inconsistente).

**Fix que funcionou de verdade:** não confiar só em `immediateRender:false`
no `fromTo`. Em vez disso, forçar explicitamente o estado baseline
correto em `time=0` com `tl.set(...)` **antes** de qualquer chamada que
agende os `fromTo()`s:

```js
// força o estado inicial real, independente de qualquer immediateRender
tl.set("#t1, #t2, #t3, #t4, #t5, #t6", { opacity: 0, backgroundColor: "#5a7896" }, 0);

// aí sim os fromTo() de entrada, agendados mais pra frente
function territoryIn(id, time) {
  tl.fromTo(id, { opacity: 0.4, backgroundColor: "#5a7896" }, { opacity: 1, backgroundColor: "#0058a8", duration: 0.33 }, time);
}
```

**Regra geral:** numa timeline pausada/seekável (contrato do
HyperFrames), sempre declare o estado em `t=0` explicitamente com
`tl.set(...)` pros elementos que só devem aparecer depois. Não dependa
de `immediateRender:false` isolado pra garantir isso.

## Outros lints encontrados (rápidos, não são "bugs" de lógica)

- `negative_z_index`: não use `z-index: -1` pra mandar um elemento pra
  trás — reordene no DOM (quem vem antes no HTML pinta primeiro).
- `nested_structure_needs_subcomposition`: estrutura de markup
  aninhada demais precisa virar sub-composição (host + `compositions/scene.html`).
- `gsap_css_transform_conflict`: não declare `transform` estático em
  CSS num elemento que também recebe tween de `x`/`y`/`scale` via GSAP —
  use `tl.set(..., {x: valorInicial}, 0)` pra declarar o estado inicial
  pelo GSAP também, em vez de CSS.
- Avisos de `container_overflow` / `escaped_container` / `canvas_overflow`
  / `panel_out_of_canvas` em nível info/warning são esperados e inerentes
  a qualquer zoom de câmera (escalar um wrapper full-bleed naturalmente
  produz uma bounding box gigante) — não bloqueiam o `check` (que passa
  com 0 erros) e podem ser ignorados.
