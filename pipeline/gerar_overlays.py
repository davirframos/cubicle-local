#!/usr/bin/env python3
"""
Pré-processamento de overlays — roda ANTES do editor.py (que continua
100% determinístico).

Lê roteiros.json. Cada roteiro pode ter uma lista opcional "overlays":
  {
    "padrao": "callout" | "recorte" | "ritmo" | "territorio" | "janela",
    "start": <segundos, absoluto, mesma linha do tempo do vídeo original>,
    "end": <segundos, absoluto>,
    "conteudo": { ... depende do padrão, ver
                  skills/motion-design-editorial/references/integracao-pipeline.md }
  }

Pra cada overlay, despacha o Tech Lead (Claude Code, modo headless/print)
com a skill motion-design-editorial + o conteúdo, pra montar e renderizar
a composição HyperFrames correspondente. Salva o mp4 resultante em
<out>/<roteiro>_<overlay>_<padrao>.mp4 e grava esse caminho de volta em
overlays[i]["arquivo"].

Escreve roteiros.overlays.json (mesma estrutura de roteiros.json, já
enriquecida com "arquivo") ao lado do roteiros.json original — é esse
arquivo que o editor.py deve receber em --roteiros quando houver
overlays.

Uso:
  python3 gerar_overlays.py \
    --roteiros roteiros.json \
    --skill-dir /home/cubicle/cubicle-local/skills/motion-design-editorial \
    --workdir /tmp/overlays-build \
    --out overlays/

Pré-requisitos no servidor: `claude` (Claude Code CLI) autenticado,
Node + npx (pro hyperframes CLI). Ver
skills/motion-design-editorial/references/ambiente.md pros workarounds
de rede/fonte/browser headless que podem ser necessários nesta infra.

NÃO TESTADO EM PRODUÇÃO: a sintaxe exata de `claude -p` abaixo deve ser
conferida contra a versão instalada no servidor (`claude --help`) antes
de confiar nisso rodando sozinho.
"""

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path


def montar_prompt(skill_dir: Path, padrao: str, duracao: float, conteudo: dict, out_mp4: Path) -> str:
    return f"""Leia {skill_dir}/SKILL.md, {skill_dir}/references/{padrao}.md,
{skill_dir}/references/ambiente.md e {skill_dir}/references/gotchas-gsap.md.

Monte uma composição HyperFrames do padrão "{padrao}" no diretório atual,
com duração {duracao:.2f}s, usando como conteúdo real (em vez do texto
de exemplo do arquivo de referência):

{json.dumps(conteudo, ensure_ascii=False, indent=2)}

Siga a spec visual, paleta, timings e técnica GSAP já documentados no
arquivo de referência — troque só o conteúdo (texto/rótulos/eventos),
não a estrutura nem os tempos dos beats, a menos que o conteúdo real
exija ajuste de tamanho/quebra de texto. Rode `npx hyperframes check .`
até passar sem erros, tire snapshots nos tempos-chave pra conferir
visualmente, depois renderize com:

  npx hyperframes render . --skill=motion-graphics -q high -o {out_mp4}

Ao final, a ÚLTIMA linha da sua resposta deve ser exatamente o caminho
absoluto do arquivo renderizado, nada mais nessa linha."""


def gerar_overlay(skill_dir: Path, overlay: dict, workdir: Path, out_mp4: Path) -> Path:
    padrao = overlay["padrao"]
    duracao = float(overlay["end"]) - float(overlay["start"])
    conteudo = overlay.get("conteudo", {})
    workdir.mkdir(parents=True, exist_ok=True)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)

    prompt = montar_prompt(skill_dir, padrao, duracao, conteudo, out_mp4)

    print(f"  -> despachando Tech Lead pra {padrao} ({duracao:.2f}s)...", file=sys.stderr)
    resultado = subprocess.run(
        ["claude", "-p", prompt, "--output-format", "text"],
        cwd=workdir, capture_output=True, text=True, timeout=900,
    )
    if resultado.returncode != 0:
        raise RuntimeError(f"Tech Lead falhou em {padrao}: {resultado.stderr.strip()[-2000:]}")

    linhas = [l.strip() for l in resultado.stdout.strip().splitlines() if l.strip()]
    caminho_reportado = Path(linhas[-1]) if linhas else None

    if caminho_reportado and caminho_reportado.exists():
        return caminho_reportado
    if out_mp4.exists():
        return out_mp4
    raise RuntimeError(
        f"Tech Lead não deixou o render em {out_mp4} nem reportou um caminho válido "
        f"(última linha: {linhas[-1] if linhas else '(vazio)'})"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roteiros", required=True, type=Path)
    ap.add_argument("--skill-dir", required=True, type=Path)
    ap.add_argument("--workdir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    args = ap.parse_args()

    args.out.mkdir(parents=True, exist_ok=True)
    data = json.loads(args.roteiros.read_text(encoding="utf-8"))
    roteiros = data["roteiros"]

    total = sum(len(r.get("overlays", [])) for r in roteiros)
    if total == 0:
        print("Nenhum overlay em roteiros.json — nada a gerar.", file=sys.stderr)
        out_json = args.roteiros.parent / f"{args.roteiros.stem}.overlays.json"
        out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        return

    feito = 0
    for ri, r in enumerate(roteiros, start=1):
        for oi, overlay in enumerate(r.get("overlays", []), start=1):
            feito += 1
            padrao = overlay["padrao"]
            print(f"[{feito}/{total}] roteiro {ri}, overlay {oi}: {padrao}", file=sys.stderr)

            out_mp4 = args.out / f"{ri:02d}_{oi:02d}_{padrao}.mp4"
            build_dir = args.workdir / f"{ri:02d}_{oi:02d}_{padrao}"
            if build_dir.exists():
                shutil.rmtree(build_dir)

            caminho = gerar_overlay(args.skill_dir, overlay, build_dir, out_mp4)
            overlay["arquivo"] = str(caminho)

    out_json = args.roteiros.parent / f"{args.roteiros.stem}.overlays.json"
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK — {feito} overlay(s) gerado(s). roteiros enriquecidos em {out_json}", file=sys.stderr)


if __name__ == "__main__":
    main()
