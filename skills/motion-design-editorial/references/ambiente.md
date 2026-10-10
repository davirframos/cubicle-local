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

### 2.1 Sandbox de agente Paperclip (`opencode_local`): sem Chromium pré-instalado, sem cache compartilhado entre agentes

Cada agente do Paperclip roda em sandbox isolado — **sem cache
compartilhado entre agentes** (confirmado empiricamente em 2026-10-09:
o agente "Teste" precisou refazer do zero um setup que o "Editor
Overlays" já tinha resolvido minutos antes). Sintoma: `check`/`lint`
passam normal (não precisam de browser), mas `snapshot`/`render` falham
com `Blocked: missing Chrome/dependencies to render`.

Checklist já validado duas vezes nesse ambiente (não precisa redescobrir
do zero — só seguir os passos, cada agente resolve no seu próprio
sandbox usando as ferramentas que já tem disponíveis):

1. **Browser**: baixe `chrome-headless-shell` versão `152.0.7977.30`
   (tag "linux64") do bucket público oficial "Chrome for Testing"
   (`chrome-for-testing-public`, path
   `152.0.7977.30/linux64/chrome-headless-shell-linux64.zip`) para
   `$HOME/.cache/hyperframes/chrome/chrome-headless-shell/linux-152.0.7977.30/`.
   Prefira uma ferramenta HTTP que siga redirect e não trave em
   conexões lentas (uma tentativa com `wget` travou; outra ferramenta
   com `-L` e timeout funcionou). Se não houver `unzip` disponível no
   sandbox, use o pacote npm `yauzl` pra extrair o `.zip`
   programaticamente. Dê permissão de execução ao binário extraído
   (`chrome-headless-shell`) depois.
2. **Libs de sistema**: baixe (sem precisar de `sudo` — o comando de
   "download apenas" do gerenciador de pacotes do SO funciona sem
   privilégio) os pacotes: `libglib2.0-0`, `libnss3`, `libnspr4`,
   `libx11-6`, `libxext6`, `libxfixes3`, `libxrandr2`, `libgbm1`,
   `libatk1.0-0`, `libatk-bridge2.0-0`, `libcups2`, `libdrm2`,
   `libpango-1.0-0`, `libcairo2`, `libasound2`, `libxcomposite1`,
   `libxdamage1`, `libxkbcommon0` para `$HOME/.cache/chrome-debs/packages/`,
   depois extraia cada pacote (sem instalar de fato — só extrair o
   conteúdo, via a ferramenta nativa do SO pra isso) para
   `$HOME/.cache/chrome-debs/rootfs/`.

   **Atenção**: `libnss3` depende do NSPR (`libnspr4`) — se faltar só o
   `libnspr4.so` (erro visto em 2026-10-09), é esse pacote que ficou de
   fora. O gerenciador de pacotes às vezes não resolve dependências
   transitivas no modo "download apenas", então baixe os pacotes
   individualmente em vez de confiar em resolução automática — confira
   com `ldd` no binário `chrome-headless-shell` extraído quais `.so`
   ainda faltam antes de desistir e pedir ajuda.
3. **Fontes**: mesma lógica pros pacotes `fonts-liberation2` e
   `fonts-dejavu-core`, extraídos no mesmo `rootfs`. Depois, crie um
   arquivo de config do fontconfig apontando pro diretório de fontes
   extraído, com aliases: `Arial`→`Liberation Sans`,
   `Georgia`/`Times New Roman`→`Liberation Serif`. **Sem isso todo
   texto renderiza em branco, sem erro visível** — só aparece ao
   inspecionar o snapshot.
4. **Variáveis de ambiente**, antes de `check`/`snapshot`/`render`:
   - `HYPERFRAMES_BROWSER_PATH` → caminho do binário `chrome-headless-shell` extraído
   - `LD_LIBRARY_PATH` → inclui `$HOME/.cache/chrome-debs/rootfs/usr/lib/x86_64-linux-gnu` e `.../usr/lib`
   - `PATH` → inclui `$HOME/.cache/chrome-debs/rootfs/usr/bin`
   - `FONTCONFIG_FILE` → caminho do `fonts.conf` criado no passo 3

Antes de gastar tempo tentando `apt install` direto (não tem `sudo`
nesse sandbox) ou um download automático diferente, siga esse checklist
— já foi validado duas vezes.

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
