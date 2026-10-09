# Padrão: Recorte

"Cutout": uma letra monumental + silhuetas de multidão sobre um card
claro, com a câmera dando push-in e depois voltando pro plano aberto.

## Spec visual

- Timeline: **5.00s** total (duração do host), cena principal usa até 4.80s.
- Paleta: fundo do card `#e9e7e0` sobre canvas `#f4f2ec`, forma/letra em
  vermelho `#cd3647`, silhuetas em `#1f2224` / `#3a3a36` (alternadas).
- `#card` é um quadrado 820x820 centralizado — **raiz de coordenadas
  locais**: tudo dentro dele (`#letter`, `#crowd`, `#ground`) usa
  `top`/`left` relativos ao card, não ao canvas 1080x1920 inteiro.

## Beats

| Tempo | Beat |
| --- | --- |
| 0.00–0.30s | Entrada: letra desliza de fora (direita→centro, `x: 900→0`), multidão+chão deslizam de fora (esquerda→centro, `x: -900→0`). Sem fade, só slide. |
| 0.30–2.30s | Câmera: push-in, `#camera scale: 1 → 1.18`, ease `power1.inOut`, 2s |
| 2.30–4.50s | Câmera: zoom-out pro plano aberto, `scale: 1.18 → 0.92`, ease `power1.inOut`, 2.2s |
| 4.50–4.80s | Saída: slide vertical pra próxima faixa, `#root yPercent: 0 → -100`, ease `power2.in`, 0.3s |

## Bug real encontrado (coordenadas locais vs. canvas)

Na primeira implementação, `#letter`/`#ground`/`#crowd` estavam
posicionados com `top`/`left` relativos ao `#camera` (que cobre o
canvas 1080x1920 inteiro via `inset:0`) em vez de relativos ao `#card`
(820x820 local). Isso causava desalinhamento severo e corte visual
errado durante o push-in.

**Fix:** aninhar `#letter`, `#ground`, `#crowd` como filhos de `#card`
(que é `position:absolute`, estabelecendo o containing block) e
reposicioná-los em coordenadas locais ao card — ver código funcional
abaixo. Ver também `gotchas-gsap.md` #1.

## Código de referência (testado, `check` passa)

```html
<div id="root" data-composition-id="recorte" data-width="1080" data-height="1920">
  <div id="camera">
    <div id="card">
      <p id="letter">OK</p>
      <div id="ground"></div>
      <div id="crowd">
        <div class="person" style="left:0px; height:70px;"></div>
        <!-- ... mais pessoas, left incrementando ~52-56px, height variando 56-74px ... -->
      </div>
    </div>
  </div>
</div>
```

```js
const tl = gsap.timeline({ paused: true });

tl.fromTo("#letter", { x: 900 }, { x: 0, duration: 0.3, ease: "power2.out" }, 0);
tl.fromTo("#crowd, #ground", { x: -900 }, { x: 0, duration: 0.3, ease: "power2.out" }, 0);

tl.fromTo("#camera", { scale: 1 }, { scale: 1.18, duration: 2, ease: "power1.inOut" }, 0.3);
tl.to("#camera", { scale: 0.92, duration: 2.2, ease: "power1.inOut" }, 2.3);

tl.to("#root", { yPercent: -100, duration: 0.3, ease: "power2.in" }, 4.5);
```

CSS chave: `#card { position:absolute; left:50%; top:50%; width:820px; height:820px; transform:translate(-50%,-50%); }`
e `#letter`/`#ground`/`#crowd` com `position:absolute; left:<valor local ao card>; top:<valor local ao card>;`.

## Nota do usuário

Validado mas o usuário comentou "não achei tão bonito" — a composição
funciona (pipeline validado), mas o resultado visual pode merecer
ajuste de design (tipografia da letra, proporção da multidão) antes de
usar em produção.
