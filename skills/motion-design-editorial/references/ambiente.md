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

### 2.1 Sandbox de agente Paperclip (`opencode_local`): sem Chromium pré-instalado, sem rede, sem cache compartilhado

Cada agente do Paperclip roda em sandbox isolado — **sem cache
compartilhado entre agentes** (confirmado empiricamente em 2026-10-09:
o agente "Teste" precisou refazer do zero um setup que o "Editor
Overlays" já tinha resolvido minutos antes). Sintoma: `check`/`lint`
passam normal (não precisam de browser), mas `snapshot`/`render` falham
com `Blocked: missing Chrome/dependencies to render`.

Rode isto **antes da primeira vez** que `render`/`snapshot` for chamado
num sandbox novo:

```bash
bash references/bootstrap-chrome-sandbox.sh
```

O script é idempotente (detecta o que já existe e pula) e resolve, em
sequência:
1. baixa e extrai o `chrome-headless-shell` via `curl` (não `wget` —
   trava/timeout nesse ambiente) + `yauzl` (sem `unzip` disponível)
2. baixa as libs de sistema necessárias (`libglib2.0-0`, `libnss3`,
   `libgbm1`, `libatk*`, `libx11-6`, etc.) via `apt-get download`
   (não precisa de sudo) e extrai com `dpkg-deb -x`
3. baixa `fonts-liberation2` + `fonts-dejavu-core` e gera um
   `fonts.conf` com aliases (Arial→Liberation Sans, Georgia/Times→Liberation
   Serif) — **sem isso todo texto renderiza em branco, sem erro
   visível**, só aparece no snapshot
4. exporta `HYPERFRAMES_BROWSER_PATH`, `LD_LIBRARY_PATH`, `PATH`,
   `FONTCONFIG_FILE` na sessão atual

Não tente baixar o Chrome manualmente nem `apt install` direto (sem
sudo nesse sandbox) — use o script.

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
