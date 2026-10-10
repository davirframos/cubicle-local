#!/bin/bash
# bootstrap-chrome-sandbox.sh
#
# Setup idempotente do chrome-headless-shell + libs de sistema + fontes
# necessário pro HyperFrames renderizar dentro de um sandbox de agente
# Paperclip (opencode_local). Descoberto empiricamente em 2026-10-09 por
# dois agentes diferentes (Editor Overlays/GLM e Teste/Nemotron) rodando
# o prototype do padrão "Recorte".
#
# POR QUE ISSO EXISTE:
# - Cada agente roda em sandbox ISOLADO, sem cache compartilhado entre si
#   (confirmado: o agente "Teste" teve que refazer tudo do zero mesmo
#   depois do "Editor Overlays" já ter resolvido o mesmo problema).
# - wget para storage.googleapis.com às vezes trava/timeout; curl -L
#   funcionou nos dois casos. Por isso usamos curl aqui.
# - Sem as libs do Chrome extraídas manualmente, chrome-headless-shell
#   não roda ("missing Chrome/dependencies to render").
# - Sem fontconfig configurado, os webfonts inline (data-URI woff2)
#   falham silenciosamente no headless shell e TODO texto renderiza em
#   branco (sem erro visível — só percebe no snapshot).
#
# USO:
#   source bootstrap-chrome-sandbox.sh
#   (ou: bash bootstrap-chrome-sandbox.sh && source <(bash bootstrap-chrome-sandbox.sh --print-env))
#
# Depois disso, HYPERFRAMES_BROWSER_PATH, LD_LIBRARY_PATH, PATH e
# FONTCONFIG_FILE já estão setados na sessão shell atual, prontos pro
# `npx hyperframes render` funcionar.

set -e

CHROME_VERSION="152.0.7977.30"
PREFIX="$HOME/.cache/chrome-debs/rootfs"
CHROME_DIR="$HOME/.cache/hyperframes/chrome/chrome-headless-shell/linux-${CHROME_VERSION}"
CHROME_ZIP="$CHROME_DIR/chrome-headless-shell-linux64.zip"
CHROME_BIN="$CHROME_DIR/chrome-headless-shell-linux64/chrome-headless-shell"
FONTS_CONF="$HOME/.cache/fonts.conf"
DEB_PKG_DIR="$HOME/.cache/chrome-debs/packages"

echo "=== bootstrap-chrome-sandbox: iniciando ==="

# ---------------------------------------------------------------------
# 1. chrome-headless-shell
# ---------------------------------------------------------------------
if [ -x "$CHROME_BIN" ]; then
  echo "[1/4] chrome-headless-shell já existe, pulando download. ($CHROME_BIN)"
else
  echo "[1/4] Baixando chrome-headless-shell ${CHROME_VERSION}..."
  mkdir -p "$CHROME_DIR"

  curl -L --max-time 120 -o "$CHROME_ZIP" \
    "https://storage.googleapis.com/chrome-for-testing-public/${CHROME_VERSION}/linux64/chrome-headless-shell-linux64.zip"

  # yauzl é necessário pro unzip funcionar sem o binário `unzip` instalado
  if ! npm list yauzl >/dev/null 2>&1; then
    npm install yauzl --no-save
  fi

  node -e "
    const yauzl = require('yauzl');
    const fs = require('fs');
    const path = require('path');
    const zipPath = process.argv[1];
    const outDir = process.argv[2];
    yauzl.open(zipPath, { lazyEntries: true }, (err, zipfile) => {
      if (err) throw err;
      zipfile.readEntry();
      zipfile.on('entry', (entry) => {
        const outPath = path.join(outDir, entry.fileName);
        if (/\/\$/.test(entry.fileName)) {
          fs.mkdirSync(outPath, { recursive: true });
          zipfile.readEntry();
        } else {
          fs.mkdirSync(path.dirname(outPath), { recursive: true });
          zipfile.openReadStream(entry, (err, readStream) => {
            if (err) throw err;
            const writeStream = fs.createWriteStream(outPath);
            readStream.pipe(writeStream);
            writeStream.on('close', () => zipfile.readEntry());
          });
        }
      });
      zipfile.on('end', () => console.log('extração concluída'));
    });
  " "$CHROME_ZIP" "$CHROME_DIR"

  chmod +x "$CHROME_BIN"
  echo "chrome-headless-shell instalado em $CHROME_BIN"
fi

# ---------------------------------------------------------------------
# 2. Libs de sistema (glib, nss, x11, gbm, atk, etc.)
# ---------------------------------------------------------------------
if find "$PREFIX" -name "libnss3.so*" 2>/dev/null | grep -q .; then
  echo "[2/4] Libs de sistema já extraídas, pulando. ($PREFIX)"
else
  echo "[2/4] Baixando e extraindo libs de sistema via apt-get download..."
  mkdir -p "$DEB_PKG_DIR" "$PREFIX"

  # apt-get download evita precisar de sudo/root pra instalar de fato —
  # só baixa o .deb pro diretório atual.
  (cd "$DEB_PKG_DIR" && apt-get download \
    libglib2.0-0 libnss3 libx11-6 libxext6 libxfixes3 libxrandr2 \
    libgbm1 libatk1.0-0 libatk-bridge2.0-0 libcups2 libdrm2 \
    libpango-1.0-0 libcairo2 libasound2 libxcomposite1 libxdamage1 \
    libxrandr2 libxkbcommon0 2>&1 | tail -20) || echo "aviso: alguns pacotes podem já estar disponíveis via mirror diferente"

  for deb in "$DEB_PKG_DIR"/*.deb; do
    [ -f "$deb" ] || continue
    echo "Extraindo $(basename "$deb")..."
    dpkg-deb -x "$deb" "$PREFIX"
  done

  echo "Libs extraídas em $PREFIX"
fi

# ---------------------------------------------------------------------
# 3. Fontes (fonts-liberation2 + fonts-dejavu-core) + fontconfig
# ---------------------------------------------------------------------
if [ -f "$FONTS_CONF" ]; then
  echo "[3/4] fonts.conf já existe, pulando. ($FONTS_CONF)"
else
  echo "[3/4] Baixando fontes e configurando fontconfig..."
  mkdir -p "$DEB_PKG_DIR"

  (cd "$DEB_PKG_DIR" && apt-get download fonts-liberation2 fonts-dejavu-core 2>&1 | tail -10)

  for deb in "$DEB_PKG_DIR"/fonts-*.deb; do
    [ -f "$deb" ] || continue
    echo "Extraindo $(basename "$deb")..."
    dpkg-deb -x "$deb" "$PREFIX"
  done

  FONT_DIR=$(find "$PREFIX" -name "*.ttf" -exec dirname {} \; | sort -u | head -1)

  cat > "$FONTS_CONF" << XMLEOF
<?xml version="1.0"?>
<!DOCTYPE fontconfig SYSTEM "fonts.dtd">
<fontconfig>
  <dir>${FONT_DIR}</dir>
  <cachedir>${HOME}/.cache/fontconfig</cachedir>
  <match target="pattern">
    <test name="family"><string>Arial</string></test>
    <edit name="family" mode="assign" binding="strong"><string>Liberation Sans</string></edit>
  </match>
  <match target="pattern">
    <test name="family"><string>Georgia</string></test>
    <edit name="family" mode="assign" binding="strong"><string>Liberation Serif</string></edit>
  </match>
  <match target="pattern">
    <test name="family"><string>Times New Roman</string></test>
    <edit name="family" mode="assign" binding="strong"><string>Liberation Serif</string></edit>
  </match>
</fontconfig>
XMLEOF

  mkdir -p "$HOME/.cache/fontconfig"
  echo "fonts.conf criado em $FONTS_CONF (fonte base: $FONT_DIR)"
fi

# ---------------------------------------------------------------------
# 4. Variáveis de ambiente
# ---------------------------------------------------------------------
echo "[4/4] Setando variáveis de ambiente..."

export PREFIX="$PREFIX"
export LD_LIBRARY_PATH="$PREFIX/usr/lib/x86_64-linux-gnu:$PREFIX/usr/lib:$PREFIX/usr/lib/x86_64-linux-gnu/pulseaudio:$PREFIX/usr/lib/x86_64-linux-gnu/blas:$PREFIX/usr/lib/x86_64-linux-gnu/lapack"
export PATH="$PREFIX/usr/bin:$PATH"
export HYPERFRAMES_BROWSER_PATH="$CHROME_BIN"
export FONTCONFIG_FILE="$FONTS_CONF"

echo ""
echo "=== bootstrap-chrome-sandbox: concluído ==="
echo "HYPERFRAMES_BROWSER_PATH=$HYPERFRAMES_BROWSER_PATH"
echo "FONTCONFIG_FILE=$FONTCONFIG_FILE"
echo ""
echo "Teste rápido:"
echo '  $HYPERFRAMES_BROWSER_PATH --version'
