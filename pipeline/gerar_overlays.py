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

Pra cada overlay, despacha o agente **Dev** (OpenCode, modelo grátis via
OpenRouter — Nemotron 3 Ultra por padrão, provider embutido no OpenCode,
sem precisar de conta/chave em lugar nenhum) em modo headless, com a
skill motion-design-editorial + o conteúdo, pra montar e renderizar a
composição HyperFrames correspondente. Isso é de propósito: é a etapa
que roda sem supervisão, possivelmente muitas vezes por vídeo — usar o
Tech Lead (Claude Code, assinatura paga) aqui consumiria sua assinatura
à toa. Guarde o Tech Lead pra prototipagem manual/supervisionada (como
foi feito pra validar os 5 padrões) ou pra correção pontual de um
overlay que o Dev não acertou.

Salva o mp4 resultante em <out>/<roteiro>_<overlay>_<padrao>.mp4 e grava
esse caminho de volta em overlays[i]["arquivo"].

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

  # trocar o modelo grátis (confira ids atuais com `opencode models openrouter`),
  # ou a reserva usada como fallback automático se o padrão falhar/travar:
  python3 gerar_overlays.py ... --modelo openrouter/nvidia/nemotron-3-ultra-550b-a55b:free \
                              --modelo-reserva openrouter/nvidia/nemotron-3-super-120b-a12b:free

  # caso pontual: forçar o Tech Lead (Claude Code, assinatura) num
  # overlay específico, por ex. pra corrigir um que o Dev não acertou:
  python3 gerar_overlays.py ... --agent claude

Pré-requisitos no servidor: `opencode` autenticado (basta `opencode auth
login`; o provider `openrouter` com os modelos `:free` já vem embutido,
sem precisar de ZenMux/conta separada), Node + npx (pro hyperframes
CLI). Ver skills/motion-design-editorial/references/ambiente.md pros
workarounds de rede/fonte/browser headless que podem ser necessários
nesta infra.

Testado manualmente uma vez: `opencode run --model
openrouter/nvidia/nemotron-3-ultra-550b-a55b:free "..."` respondeu
corretamente num teste simples. O fluxo completo (ler a skill, montar
GSAP, rodar check/render) ainda não foi validado de ponta a ponta — esse
modelo é bem mais fraco que Claude pra tarefa agente-longa, espere
precisar revisar mais os resultados, principalmente pros padrões já
marcados como "baixa prontidão" no integracao-pipeline.md (ritmo,
território, janela).
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


def montar_comando(agent: str, modelo: str, prompt: str) -> list:
    if agent == "opencode":
        cmd = ["opencode", "run"]
        if modelo:
            cmd += ["--model", modelo]
        cmd += [prompt]
        return cmd
    if agent == "claude":
        return ["claude", "-p", prompt, "--output-format", "text"]
    raise ValueError(f"agente desconhecido: {agent}")


def despachar(agent: str, modelo: str, prompt: str, workdir: Path, timeout: int):
    cmd = montar_comando(agent, modelo, prompt)
    return subprocess.run(cmd, cwd=workdir, capture_output=True, text=True, timeout=timeout)


def gerar_overlay(skill_dir: Path, overlay: dict, workdir: Path, out_mp4: Path,
                   agent: str, modelo: str, modelo_reserva: str, timeout: int) -> Path:
    padrao = overlay["padrao"]
    duracao = float(overlay["end"]) - float(overlay["start"])
    conteudo = overlay.get("conteudo", {})
    workdir.mkdir(parents=True, exist_ok=True)
    out_mp4.parent.mkdir(parents=True, exist_ok=True)

    prompt = montar_prompt(skill_dir, padrao, duracao, conteudo, out_mp4)

    print(f"  -> despachando {agent}/{modelo or '(padrão)'} pra {padrao} ({duracao:.2f}s)...", file=sys.stderr)
    resultado = despachar(agent, modelo, prompt, workdir, timeout)

    if resultado.returncode != 0 and agent == "opencode" and modelo_reserva:
        print(f"  -> {modelo} falhou (camada grátis esgotada?), tentando reserva {modelo_reserva}...", file=sys.stderr)
        resultado = despachar(agent, modelo_reserva, prompt, workdir, timeout)

    if resultado.returncode != 0:
        raise RuntimeError(f"Dev falhou em {padrao}: {resultado.stderr.strip()[-2000:]}")

    linhas = [l.strip() for l in resultado.stdout.strip().splitlines() if l.strip()]
    caminho_reportado = Path(linhas[-1]) if linhas else None

    if caminho_reportado and caminho_reportado.exists():
        return caminho_reportado
    if out_mp4.exists():
        return out_mp4
    raise RuntimeError(
        f"Agente não deixou o render em {out_mp4} nem reportou um caminho válido "
        f"(última linha: {linhas[-1] if linhas else '(vazio)'})"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roteiros", required=True, type=Path)
    ap.add_argument("--skill-dir", required=True, type=Path)
    ap.add_argument("--workdir", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--agent", default="opencode", choices=["opencode", "claude"],
                     help="agente a usar (padrão: opencode = Dev, grátis). 'claude' usa o Tech Lead/assinatura.")
    ap.add_argument("--modelo", default="openrouter/nvidia/nemotron-3-ultra-550b-a55b:free",
                     help="modelo passado ao agente opencode, formato provider/model "
                          "(confirme ids atuais com `opencode models openrouter`); ignorado com --agent claude")
    ap.add_argument("--modelo-reserva", default="openrouter/nvidia/nemotron-3-super-120b-a12b:free",
                     help="modelo de fallback se --modelo falhar/travar; vazio = sem fallback")
    ap.add_argument("--timeout", type=int, default=900, help="timeout em segundos por overlay")
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

            caminho = gerar_overlay(
                args.skill_dir, overlay, build_dir, out_mp4,
                args.agent, args.modelo, args.modelo_reserva, args.timeout,
            )
            overlay["arquivo"] = str(caminho)

    out_json = args.roteiros.parent / f"{args.roteiros.stem}.overlays.json"
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK — {feito} overlay(s) gerado(s). roteiros enriquecidos em {out_json}", file=sys.stderr)


if __name__ == "__main__":
    main()
