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

Pra cada overlay, cria uma ISSUE no Paperclip (via `paperclipai issue
create`) atribuída a um agente real do seu escritório — por padrão o
agente "Editor Overlays" (OpenCode + Nemotron 3 Ultra grátis via
OpenRouter). Confirmado na prática: criar a issue com
--assignee-agent-id já dispara a run sozinha, sem precisar de
`agent wake` nem nada parecido — o Paperclip pega a issue automaticamente
em segundos.

O script espera a issue chegar em status "done" e confere se o mp4
apareceu no caminho absoluto que foi pedido no prompt (em vez de tentar
interpretar a resposta em texto do agente — é mais simples e mais
confiável: o próprio `hyperframes render -o <caminho>` já garante que o
arquivo existe nesse caminho exato se deu certo). Salva o caminho em
overlays[i]["arquivo"].

Escreve roteiros.overlays.json (mesma estrutura de roteiros.json, já
enriquecida com "arquivo") ao lado do roteiros.json original — é esse
arquivo que o editor.py deve receber em --roteiros quando houver
overlays.

Uso:
  python3 gerar_overlays.py \
    --roteiros roteiros.json \
    --skill-dir /home/cubicle/cubicle-local/skills/motion-design-editorial \
    --company-id 2402a146-f7d1-4af7-8396-acacadd98e13 \
    --agent-id b107fce3-6e9f-4895-ae60-7627dc1d2028 \
    --out overlays/

  # com um agente de reserva (ex: Tech Lead/Claude Code) se o principal
  # não deixar o arquivo pronto (erro, travou, ou "done" sem renderizar):
  python3 gerar_overlays.py ... --agent-id-reserva <id-do-tech-lead>

Pré-requisitos no servidor: `paperclipai` autenticado (fluxo normal de
board auth — se pedir, abra a URL de aprovação no navegador, trocando
"localhost" pelo IP do container), o agente já criado no Paperclip com
adapter OpenCode + modelo grátis (ver
skills/motion-design-editorial/references/integracao-pipeline.md), Node
+ npx (pro hyperframes CLI) disponível no ambiente onde esse agente
roda. Ver skills/motion-design-editorial/references/ambiente.md pros
workarounds de rede/fonte/browser headless que podem ser necessários.

Validado manualmente até aqui: criar issue → run dispara sozinha →
status chega em "done" (campo `status` do `paperclipai issue get`,
confirmado contra uma issue real). NÃO validado ainda: o fluxo completo
de gerar um overlay de verdade (ler a skill, montar GSAP, rodar
check/render) — só testamos uma issue trivial ("diga oi"). Rode um
`callout` simples primeiro antes de confiar em produção.
"""

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Optional

# status que ainda consideramos "em andamento" — qualquer outra coisa
# que não seja "done" é tratada como terminal/falha. Não temos a lista
# completa de status possíveis do Paperclip; ajuste aqui se aparecer um
# novo status ativo que o script não deveria tratar como erro.
STATUS_EM_ANDAMENTO = {"todo", "in_progress", "queued", "running", "blocked", "in_review"}
STATUS_SUCESSO = "done"


def paperclipai(args: list, esperar_json: bool = True):
    cmd = ["paperclipai", *args]
    if esperar_json and "--json" not in cmd:
        cmd.append("--json")
    resultado = subprocess.run(cmd, capture_output=True, text=True)
    if resultado.returncode != 0:
        raise RuntimeError(f"paperclipai {' '.join(args)} falhou: {resultado.stderr.strip()[-2000:]}")
    if not esperar_json:
        return resultado.stdout
    try:
        return json.loads(resultado.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"paperclipai {' '.join(args)} não devolveu JSON válido: {e}\n{resultado.stdout[:500]}")


def montar_prompt(skill_dir: Path, padrao: str, duracao: float, conteudo: dict,
                   build_dir: Path, out_mp4: Path) -> str:
    return f"""Leia {skill_dir}/SKILL.md, {skill_dir}/references/{padrao}.md,
{skill_dir}/references/ambiente.md e {skill_dir}/references/gotchas-gsap.md.

Crie o diretório {build_dir} (mkdir -p se não existir) e monte ali uma
composição HyperFrames do padrão "{padrao}", com duração {duracao:.2f}s,
usando como conteúdo real (em vez do texto de exemplo do arquivo de
referência):

{json.dumps(conteudo, ensure_ascii=False, indent=2)}

Siga a spec visual, paleta, timings e técnica GSAP já documentados no
arquivo de referência — troque só o conteúdo (texto/rótulos/eventos),
não a estrutura nem os tempos dos beats, a menos que o conteúdo real
exija ajuste de tamanho/quebra de texto. Rode `npx hyperframes check .`
dentro de {build_dir} até passar sem erros, tire snapshots nos
tempos-chave pra conferir visualmente, depois renderize com:

  npx hyperframes render . --skill=motion-graphics -q high -o {out_mp4}

O caminho de saída {out_mp4} é absoluto e obrigatório — é assim que o
pipeline confirma que o overlay foi gerado. Confirme ao final que esse
arquivo existe antes de encerrar a task."""


def criar_issue(company_id: str, agent_id: str, titulo: str, prompt: str):
    data = paperclipai([
        "issue", "create", "-C", company_id,
        "--title", titulo,
        "--description", prompt,
        "--assignee-agent-id", agent_id,
    ])
    return data["id"], data.get("identifier", data["id"])


def esperar_issue(issue_id: str, timeout: int, poll_every: int):
    deadline = time.time() + timeout
    ultimo_status = None
    while time.time() < deadline:
        issue = paperclipai(["issue", "get", issue_id])
        ultimo_status = issue.get("status")
        if ultimo_status == STATUS_SUCESSO:
            return issue
        if ultimo_status not in STATUS_EM_ANDAMENTO:
            raise RuntimeError(f"issue {issue_id} terminou com status inesperado: {ultimo_status!r}")
        time.sleep(poll_every)
    raise TimeoutError(f"issue {issue_id} não chegou a 'done' em {timeout}s (último status: {ultimo_status!r})")


def tentar_extrair_caminho_dos_comentarios(issue_id: str) -> Optional[Path]:
    """Fallback: se o mp4 esperado não existe, procura um caminho
    existente na última linha de algum comentário do agente."""
    comentarios = paperclipai(["issue", "comments", issue_id, "--order", "asc"])
    for c in reversed(comentarios):
        if c.get("authorType") != "agent":
            continue
        linhas = [l.strip() for l in c.get("body", "").strip().splitlines() if l.strip()]
        if not linhas:
            continue
        candidato = Path(linhas[-1])
        if candidato.exists():
            return candidato
    return None


def gerar_overlay(company_id: str, agent_id: str, agent_id_reserva: str,
                   skill_dir: Path, overlay: dict, build_dir: Path, out_mp4: Path,
                   timeout: int, poll_every: int) -> Path:
    padrao = overlay["padrao"]
    duracao = float(overlay["end"]) - float(overlay["start"])
    conteudo = overlay.get("conteudo", {})
    out_mp4.parent.mkdir(parents=True, exist_ok=True)

    prompt = montar_prompt(skill_dir, padrao, duracao, conteudo, build_dir, out_mp4)
    titulo = f"Overlay {padrao} — {out_mp4.stem}"

    for tentativa_agent_id in filter(None, [agent_id, agent_id_reserva]):
        issue_id, identificador = criar_issue(company_id, tentativa_agent_id, titulo, prompt)
        print(f"  -> issue {identificador} criada (agente {tentativa_agent_id}), aguardando...", file=sys.stderr)
        try:
            esperar_issue(issue_id, timeout, poll_every)
        except (RuntimeError, TimeoutError) as e:
            print(f"  -> {identificador} não terminou bem: {e}", file=sys.stderr)
            if tentativa_agent_id == agent_id and agent_id_reserva:
                print("  -> tentando com o agente de reserva...", file=sys.stderr)
                continue
            raise

        if out_mp4.exists() and out_mp4.stat().st_size > 0:
            return out_mp4

        caminho_alternativo = tentar_extrair_caminho_dos_comentarios(issue_id)
        if caminho_alternativo:
            return caminho_alternativo

        msg = f"issue {identificador} terminou 'done' mas {out_mp4} não existe — confira a issue no Paperclip"
        if tentativa_agent_id == agent_id and agent_id_reserva:
            print(f"  -> {msg}, tentando com o agente de reserva...", file=sys.stderr)
            continue
        raise RuntimeError(msg)

    raise RuntimeError(f"não foi possível gerar o overlay {padrao} ({out_mp4})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--roteiros", required=True, type=Path)
    ap.add_argument("--skill-dir", required=True, type=Path,
                     help="caminho absoluto de skills/motion-design-editorial no servidor")
    ap.add_argument("--company-id", required=True, help="id da empresa no Paperclip (`paperclipai company list`)")
    ap.add_argument("--agent-id", required=True, help="id do agente que vai gerar os overlays (ex: Editor Overlays)")
    ap.add_argument("--agent-id-reserva", default="",
                     help="id de um agente alternativo (ex: Tech Lead) se o principal falhar; vazio = sem fallback")
    ap.add_argument("--build-dir", default="/tmp/overlays-build", type=Path,
                     help="diretório base (no host onde o agente roda) onde cada overlay monta seu projeto HyperFrames")
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--timeout", type=int, default=1200, help="timeout em segundos por overlay (padrão: 20min)")
    ap.add_argument("--poll-every", type=int, default=15, help="intervalo em segundos entre checagens de status")
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
            build_dir = args.build_dir / f"{ri:02d}_{oi:02d}_{padrao}"

            caminho = gerar_overlay(
                args.company_id, args.agent_id, args.agent_id_reserva,
                args.skill_dir, overlay, build_dir, out_mp4,
                args.timeout, args.poll_every,
            )
            overlay["arquivo"] = str(caminho)

    out_json = args.roteiros.parent / f"{args.roteiros.stem}.overlays.json"
    out_json.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"OK — {feito} overlay(s) gerado(s). roteiros enriquecidos em {out_json}", file=sys.stderr)


if __name__ == "__main__":
    main()
