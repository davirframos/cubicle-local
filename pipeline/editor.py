#!/usr/bin/env python3
"""
Editor — etapa sem IA do pipeline do canal dark (Paperclip).

Recebe:
  - o vídeo original (mp4)
  - a transcrição com timestamps no formato "00:00:00 texto..." (uma por linha)
  - o JSON de roteiros produzido pelo agente Roteirista (start/end/titulo/legenda/descricao),
    opcionalmente enriquecido com "overlays" (ver gerar_overlays.py e
    skills/motion-design-editorial/references/integracao-pipeline.md)

Produz, para cada roteiro:
  - um corte vertical 1080x1920 (9:16), legendado (burn-in), pronto pra postar
  - se o roteiro tiver overlays com "arquivo" preenchido, o trecho
    correspondente do corte é substituído pela composição gerada (o
    áudio original continua por baixo, sem corte — é um insert/cutaway
    visual, não uma camada translúcida)
  - salvo em prontos/<numero>_<titulo-slug>.mp4

Uso:
  python3 editor.py --video video.mp4 --transcricao transcricao.txt --roteiros roteiros.json --out prontos/
  python3 editor.py --video video.mp4 --transcricao transcricao.txt --roteiros roteiros.overlays.json --out prontos/
"""

import argparse
import json
import re
import subprocess
import sys
import unicodedata
from pathlib import Path


def slugify(text: str, max_len: int = 40) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    text = re.sub(r"[\s_-]+", "-", text)
    return text[:max_len].strip("-") or "corte"


def parse_transcricao(path: Path):
    """Parseia linhas 'HH:MM:SS texto' (ou MM:SS) em uma lista de (segundos, texto)."""
    linhas = []
    pattern = re.compile(r"^(\d{1,2}):(\d{2}):(\d{2})\s+(.*)$")
    pattern_mmss = re.compile(r"^(\d{1,2}):(\d{2})\s+(.*)$")
    for raw in path.read_text(encoding="utf-8").splitlines():
        raw = raw.strip()
        if not raw:
            continue
        m = pattern.match(raw)
        if m:
            h, mnt, s, texto = m.groups()
            seg = int(h) * 3600 + int(mnt) * 60 + int(s)
            linhas.append((seg, texto))
            continue
        m = pattern_mmss.match(raw)
        if m:
            mnt, s, texto = m.groups()
            seg = int(mnt) * 60 + int(s)
            linhas.append((seg, texto))
    return linhas


def build_srt_for_range(linhas, start: float, end: float, out_srt: Path):
    """Gera um .srt cobrindo [start, end), com timestamps relativos ao corte."""
    trecho = [(seg, txt) for seg, txt in linhas if start <= seg < end]
    if not trecho:
        # sem transcrição nesse intervalo: cria um srt vazio (sem legenda) em vez de falhar
        out_srt.write_text("", encoding="utf-8")
        return False

    entries = []
    for i, (seg, txt) in enumerate(trecho):
        rel_start = max(0.0, seg - start)
        # fim = início da próxima linha, ou +3s se for a última
        if i + 1 < len(trecho):
            rel_end = trecho[i + 1][0] - start
        else:
            rel_end = min(end - start, rel_start + 3.0)
        entries.append((rel_start, rel_end, txt))

    def fmt(t: float) -> str:
        h = int(t // 3600)
        m = int((t % 3600) // 60)
        s = int(t % 60)
        ms = int((t - int(t)) * 1000)
        return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

    lines = []
    for idx, (rs, re_, txt) in enumerate(entries, start=1):
        lines.append(str(idx))
        lines.append(f"{fmt(rs)} --> {fmt(re_)}")
        lines.append(txt)
        lines.append("")
    out_srt.write_text("\n".join(lines), encoding="utf-8")
    return True


def overlays_validos_no_corte(overlays, start: float, end: float):
    """Filtra/recorta os overlays de um roteiro pros limites do corte, em
    tempo relativo ao início do corte. Overlays sem "arquivo" (não
    gerados ainda) são ignorados."""
    duracao = end - start
    validos = []
    for ov in overlays or []:
        if not ov.get("arquivo"):
            continue
        rel_start = max(0.0, float(ov["start"]) - start)
        rel_end = min(duracao, float(ov["end"]) - start)
        if rel_end > rel_start:
            validos.append((ov["arquivo"], rel_start, rel_end))
    return validos


def cortar_e_legendar(video: Path, start: float, end: float, srt: Path, has_srt: bool, overlays, out_mp4: Path):
    duracao = end - start

    # vertical 1080x1920: escala pela altura e corta as bordas laterais (centro),
    # ou faz letterbox com blur de fundo se a fonte já for mais estreita que 9:16.
    crop = "scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920"

    base = f"[0:v]{crop}"
    if has_srt:
        srt_escaped = str(srt).replace("\\", "/").replace(":", "\\:")
        base += (
            f",subtitles='{srt_escaped}':force_style="
            "'FontName=Arial,FontSize=20,PrimaryColour=&H00FFFFFF,"
            "OutlineColour=&H00000000,BorderStyle=3,Outline=2,Alignment=2,MarginV=90'"
        )

    inputs = ["-ss", str(start), "-to", str(end), "-i", str(video)]
    overlays_validos = overlays_validos_no_corte(overlays, start, end)

    if not overlays_validos:
        cmd = [
            "ffmpeg", "-y", *inputs,
            "-vf", base[len("[0:v]"):],
            "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
            "-c:a", "aac", "-b:a", "160k",
            str(out_mp4),
        ]
        subprocess.run(cmd, check=True, capture_output=True, text=True)
        return

    # overlays: substitui o trecho [rel_start, rel_end) do vídeo pela
    # composição gerada (fundo opaco, cobre o frame inteiro), áudio
    # original continua — ver references/integracao-pipeline.md
    filtro = [f"{base}[base]"]
    atual = "[base]"
    for i, (arquivo, rel_start, rel_end) in enumerate(overlays_validos, start=1):
        inputs += ["-itsoffset", f"{rel_start:.3f}", "-i", str(arquivo)]
        filtro.append(f"[{i}:v]format=yuva420p,scale=1080:1920[ov{i}]")
        destino = f"[tmp{i}]"
        filtro.append(
            f"{atual}[ov{i}]overlay=enable='between(t,{rel_start:.3f},{rel_end:.3f})'{destino}"
        )
        atual = destino

    cmd = [
        "ffmpeg", "-y", *inputs,
        "-filter_complex", ";".join(filtro),
        "-map", atual, "-map", "0:a",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "20",
        "-c:a", "aac", "-b:a", "160k",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True, capture_output=True, text=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--video", required=True, type=Path)
    ap.add_argument("--transcricao", required=True, type=Path)
    ap.add_argument("--roteiros", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)

    linhas = parse_transcricao(args.transcricao)
    data = json.loads(args.roteiros.read_text(encoding="utf-8"))
    roteiros = data["roteiros"]

    resultado = []
    for i, r in enumerate(roteiros, start=1):
        start, end = float(r["start"]), float(r["end"])
        titulo = r.get("titulo", f"corte-{i}")
        slug = slugify(titulo)
        srt_path = args.out / f"{i:02d}_{slug}.srt"
        has_srt = build_srt_for_range(linhas, start, end, srt_path)

        overlays = r.get("overlays", [])
        n_overlays = len(overlays_validos_no_corte(overlays, start, end))

        out_mp4 = args.out / f"{i:02d}_{slug}.mp4"
        sufixo = f" (+{n_overlays} overlay(s))" if n_overlays else ""
        print(f"[{i}/{len(roteiros)}] cortando {start:.0f}s-{end:.0f}s -> {out_mp4.name}{sufixo}", file=sys.stderr)
        cortar_e_legendar(args.video, start, end, srt_path, has_srt, overlays, out_mp4)

        resultado.append({
            "arquivo": str(out_mp4),
            "titulo": titulo,
            "legenda": r.get("legenda", ""),
            "descricao": r.get("descricao", ""),
            "start": start,
            "end": end,
            "overlays": n_overlays,
        })

    manifest = args.out / "manifest.json"
    manifest.write_text(json.dumps({"prontos": resultado}, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK — {len(resultado)} vídeo(s) em {args.out}, manifest em {manifest}", file=sys.stderr)


if __name__ == "__main__":
    main()
