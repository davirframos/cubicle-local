# cubicle-local

Meu escritório de agentes de IA rodando no servidor caseiro (Proxmox), inspirado no Cubicle do vídeo do Bero.
Tudo grátis: só software open source, camadas gratuitas de API e as assinaturas que eu já tenho (Claude e Gemini).

## Como funciona

```
Navegador / celular
      |
Cubicle (porta 3200)    escritório visual: mesas, quem trabalha, quem levantou a mão
      |  lê o status
Paperclip (porta 3100)  a "empresa": agentes, cargos, tarefas, skills
      |  dispara
Agentes (CLIs)          Claude Code | OpenCode | Gemini CLI
      |  usam
Modelos (nuvem)         Claude (assinatura) | Kimi K3 grátis | Gemini (assinatura) | Kimi K2.6 grátis no NVIDIA NIM (reserva)
```

O servidor (i5-3210M, 8 GB de RAM, sem GPU) não roda modelos de IA. Ele roda só o escritório, num container LXC leve.

## O time

| Agente | Ferramenta | Modelo | Papel |
|---|---|---|---|
| Tech Lead | Claude Code | Claude (assinatura) | planeja, divide tarefas, revisa |
| Dev | OpenCode | Kimi K3 grátis (OpenCode Zen / ZenMux) | executa o trabalho pesado |
| Pesquisador | Gemini CLI | Gemini (assinatura) | pesquisa e lê documentos longos |
| Reserva | OpenCode | Kimi K2.6 grátis (NVIDIA NIM) | entra quando a camada grátis do K3 acabar |

## Instalação

1. Criar o container no Proxmox: [setup/criar-lxc.md](setup/criar-lxc.md)
2. Dentro do container: `bash scripts/install.sh`
3. Fazer login em cada ferramenta e criar os agentes no Paperclip: [setup/configurar-agentes.md](setup/configurar-agentes.md)

## Skills

Cada skill é uma pasta em `skills/` com um `SKILL.md` (nome, descrição e instruções), além de scripts opcionais.
Exemplo: [skills/resumo-do-servidor](skills/resumo-do-servidor/SKILL.md).

## Pipeline do canal dark

Edição automática de vídeo, em `pipeline/`:

```
roteiros.json (Roteirista, com "overlays" opcionais)
      |
pipeline/gerar_overlays.py   despacha o Tech Lead (skill motion-design-editorial)
      v                       pra renderizar cada overlay
roteiros.overlays.json
      |
pipeline/editor.py            100% determinístico: corta, legenda e
      v                       compõe os overlays prontos com FFmpeg
prontos/*.mp4
```

Ver [skills/motion-design-editorial/references/integracao-pipeline.md](skills/motion-design-editorial/references/integracao-pipeline.md)
pro schema de `overlays` e o contrato de conteúdo de cada padrão.
