# Workarounds de ambiente

Encontrados validando os 5 padrões num container com proxy de allowlist
de rede (provavelmente similar ao ambiente de CI/execução do Paperclip —
confirme no servidor real se os mesmos bloqueios se aplicam).

## 1. CDN do GSAP bloqueado

Os exemplos do HyperFrames referenciam GSAP via `cdn.jsdelivr.net`, que
pode estar bloqueado (403 no CONNECT tunnel). Workaround: instalar local
e referenciar o arquivo direto, sem CDN:

```bash
npm install gsap@3.14.2 --no-save
```

E no `index.html`:
```html
<script src="node_modules/gsap/dist/gsap.min.js"></script>
```

## 2. Download automático do `chrome-headless-shell` bloqueado

O HyperFrames tenta baixar um Chromium headless shell de
`storage.googleapis.com` na primeira execução; pode dar 403. Se o
ambiente já tiver um Chromium headless do Playwright pré-instalado,
aponte pra ele via variável de ambiente antes de rodar `check`/`snapshot`/`render`:

```bash
export HYPERFRAMES_BROWSER_PATH=/opt/pw-browsers/chromium_headless_shell-1194/chrome-linux/headless_shell
```

(ajuste o caminho pro que existir de fato no servidor — rode `find /opt -iname 'headless_shell'` ou equivalente pra confirmar).

## 3. Fontes do manual não disponíveis no ambiente de render

O manual original usa `'Archivo Narrow'` e `'JetBrains Mono'` em alguns
slides. Esses `@font-face` não existem no ambiente de render e geram o
lint error `font_family_without_font_face`. Fallbacks usados nos
protótipos:
- `'Archivo Narrow'` → `Arial, Helvetica, sans-serif`
- `'JetBrains Mono'` → `'Courier New', monospace`

Se o servidor real tiver essas fontes instaladas (ou declaradas via
`@font-face` com arquivo local), pode usar as originais — só evite
depender de uma fonte sem `@font-face` declarado, o linter reclama.
