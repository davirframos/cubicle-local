# Integração com o pipeline do canal dark

Como os 5 padrões entram no pipeline Curador → Roteirista → **Editor**
→ Revisor → Saída, em duas etapas separadas:

```
roteiros.json (Roteirista, com overlays opcionais)
        |
pipeline/gerar_overlays.py   <- ETAPA COM IA: cria uma issue no Paperclip
        |                        por overlay, atribuída ao agente
        v                        "Editor Overlays" (ou outro), que gera
                                  a composição e renderiza
roteiros.overlays.json (igual, mas cada overlay ganha "arquivo": caminho do mp4)
        |
pipeline/editor.py           <- continua 100% determinístico: só lê os
        |                        mp4s prontos e sobrepõe com FFmpeg
        v
prontos/*.mp4
```

**Por que separado:** `editor.py` foi desenhado pra ser a "etapa sem IA"
do pipeline (determinística, reexecutável, sem custo de modelo). Gerar
um overlay exige um agente (precisa ler a spec, montar a composição
HyperFrames, rodar `check`/`render`) — então isso vira um passo próprio,
que roda antes e produz arquivos prontos. O Editor nunca chama um
modelo.

## Como a geração funciona de verdade (validado na prática)

`gerar_overlays.py` **não** chama `opencode`/`claude` direto por
`subprocess` — ele passa pelo Paperclip de verdade, como qualquer
trabalho do seu escritório:

1. Cria uma **issue** via `paperclipai issue create -C <company-id>
   --assignee-agent-id <agent-id> --description "<prompt>"`.
2. **Confirmado:** isso já dispara a run sozinho — o Paperclip pega a
   issue automaticamente em segundos (`invocationSource: "automation"`),
   sem precisar de `agent wake` nem nada manual.
3. O script faz polling em `paperclipai issue get <issue-id> --json`
   até o campo `status` virar `"done"` (confirmado como o valor
   terminal de sucesso).
4. Em vez de tentar interpretar a resposta em texto do agente, o script
   confere se o mp4 apareceu no **caminho absoluto** que foi pedido no
   prompt (`npx hyperframes render . -o <caminho>`) — mais simples e
   confiável. Só cai pra ler os comentários da issue
   (`paperclipai issue comments`) como fallback se o arquivo não
   aparecer.

Isso aparece no Cubicle como trabalho real do agente, com a conversa
completa (prompt → resposta → "Task completed") — dá pra acompanhar
pela própria UI, não só pelo terminal.

### Por que um agente dedicado (Editor Overlays) e não o Tech Lead

Esta etapa roda sem supervisão, potencialmente várias vezes por vídeo —
é exatamente o tipo de trabalho repetitivo que não deveria consumir a
assinatura do Claude. Criamos um agente novo, **Editor Overlays**,
adapter OpenCode, modelo `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free`
(provider OpenRouter já embutido no OpenCode, sem ZenMux nem Kimi Code
— ver nota histórica abaixo), "Skip permissions" ligado (pra não travar
esperando aprovação numa run sem ninguém olhando).

`gerar_overlays.py` recebe `--agent-id` (o Editor Overlays) e
opcionalmente `--agent-id-reserva` (ex: o Tech Lead/Claude Code) — se o
principal não deixar o mp4 pronto (erro, timeout, ou "done" sem
renderizar), o script cria uma segunda issue no agente de reserva
automaticamente.

(Nota histórica: cogitamos primeiro Kimi K3 via ZenMux e depois o Kimi
Code CLI nativo — mas Kimi Code exige assinatura paga da Moonshot, e o
Kimi K3 "grátis" documentado no README original não ficou confirmado
contra a doc oficial do ZenMux. Os modelos `:free` do OpenRouter, já
embutidos no OpenCode sem nenhum cadastro extra, foram o caminho mais
simples e confirmado.)

Nemotron 3 Ultra é bem mais fraco que Claude pra tarefa agente-longa
(ler várias referências, montar GSAP, rodar check/render, depurar erro
de lint) — espere precisar revisar mais os resultados, principalmente
nos padrões já marcados como baixa prontidão abaixo.

**Importante sobre o resultado visual:** os 5 padrões validados têm
fundo opaco (telas cheias — mapa, cartão, etc.), não são overlays
translúcidos. A composição no Editor funciona como um **insert/cutaway**:
durante a janela do overlay, o vídeo original é *substituído* pela
composição gerada (o áudio original continua por baixo, sem corte) —
não é uma camada semi-transparente por cima da gravação. Se no futuro
quiser overlays translúcidos (gráfico flutuando sobre a tela, sem
substituir o frame), isso exige recompor os 5 padrões com fundo
transparente e renderizar com `--format webm`/`mov` — não é o que está
implementado agora.

## Schema: `overlays` em cada roteiro

`roteiros.json` (saída do Roteirista) ganha um campo opcional
`overlays` por roteiro:

```json
{
  "roteiros": [
    {
      "start": 120.5,
      "end": 168.0,
      "titulo": "...",
      "legenda": "...",
      "descricao": "...",
      "overlays": [
        {
          "padrao": "callout",
          "start": 125.0,
          "end": 129.0,
          "conteudo": { "rotulo": "SOC", "frase": "Invasão detectada em 40 segundos" }
        }
      ]
    }
  ]
}
```

- `start`/`end` são **absolutos**, na mesma linha do tempo do vídeo
  original (igual ao `start`/`end` do roteiro, não relativos ao corte).
- `end - start` deve bater com a duração fixa do padrão (ver tabela no
  `SKILL.md` principal) — o Roteirista deve respeitar essas durações ao
  escolher o `start`, não esticar/encolher o padrão.
- `padrao` é um dos 5 ids: `callout`, `recorte`, `ritmo`, `territorio`, `janela`.
- `conteudo` é livre por padrão (ver "Contrato de conteúdo" abaixo) — o
  agente usa isso pra substituir o texto de exemplo de cada referência
  pelo conteúdo real, mantendo a estrutura/timing/paleta.

## Contrato de conteúdo por padrão (o que o Roteirista deve preencher)

| Padrão | Campos de `conteudo` | Prontidão pra geração automática |
| --- | --- | --- |
| `callout` | `rotulo` (sigla curta), `frase` (texto de destaque) | **Alta** — só texto, estrutura genérica |
| `recorte` | `letra` (1-2 caracteres/palavra curta pra forma monumental) | **Média** — a letra é fácil de trocar; multidão/chão são decorativos fixos |
| `ritmo` | `descricao` (o que as duas "silhuetas" representam) — **não gera imagens reais**, usa formas placeholder | **Baixa pra conteúdo real** — pra usar com imagens/fotos de verdade precisa passar por `/media-use` antes (sourcing de imagem), isso ainda não está encadeado aqui |
| `territorio` | `eventos`: lista de `{nome, ano, descricao}` — mas as posições/formas no mapa são desenhadas à mão (coordenadas de pixel) pro caso específico de expansão territorial dos EUA | **Baixa** — é um protótipo ilustrativo de UM caso específico, não um gerador genérico de "qualquer mapa, qualquer território"; adaptar pra outro mapa/assunto exige o agente redesenhar as formas, não só trocar texto |
| `janela` | `evento_nome`, `evento_tempo`, `reacao_descricao` (o que muda no mapa de fundo) | **Baixa** — mesmo caso do território: o mapa/país de fundo é um placeholder específico (URSS), não genérico |

**Na prática hoje:** `callout` e `recorte` são os mais seguros pra
automação sem supervisão com um modelo mais fraco (Nemotron 3 Ultra).
`ritmo`, `territorio` e `janela` tendem a precisar de revisão humana do
resultado (ou de mais trabalho de design) antes de confiar neles em
produção, porque o conteúdo de exemplo validado era bem específico — o
agente vai ter que *adaptar* a estrutura visual pro assunto real, não só
preencher campos. Se o Editor Overlays travar muito num desses três,
vale configurar `--agent-id-reserva` com o Tech Lead pra esses casos.

## Scripts

- `pipeline/gerar_overlays.py` — lê `roteiros.json`, cria uma issue no
  Paperclip por overlay (agente padrão: Editor Overlays, com
  `--agent-id-reserva` opcional pra um fallback tipo Tech Lead), espera
  `status: "done"`, confere o mp4 no caminho absoluto pedido, grava os
  caminhos e escreve `roteiros.overlays.json` com `overlays[i]["arquivo"]`
  preenchido.
- `pipeline/editor.py` — o Editor original + composição: se um roteiro
  tem `overlays` com `"arquivo"` preenchido, substitui o trecho
  correspondente do corte final pelo mp4 do overlay (via filtro
  `overlay` do FFmpeg, mantendo o áudio original).

## IDs de referência (ambiente atual, podem mudar)

- Company-id ("IAs Locais"): `2402a146-f7d1-4af7-8396-acacadd98e13`
- Agent-id (Editor Overlays): `b107fce3-6e9f-4895-ae60-7627dc1d2028`

(Confirme sempre com `paperclipai company list` / `paperclipai agent
list -C <company-id>` antes de rodar em produção — esses ids são de
quando validamos o mecanismo, podem mudar se o agente for recriado.)

## O que já foi confirmado, e o que ainda não

**Confirmado, com uma issue real de teste:**
- Criar a issue com `--assignee-agent-id` já dispara a run sozinha.
- O campo `status` chega em `"done"` quando termina (via
  `paperclipai issue get <id> --json`).
- O agente (Nemotron 3 Ultra) responde corretamente a um prompt simples.

**Ainda não testado de ponta a ponta:**
- O fluxo completo de gerar um overlay de verdade (ler os 4 arquivos de
  referência da skill, montar a composição GSAP, rodar `hyperframes
  check`/`snapshot`/`render`, corrigir um erro de lint sozinho) — só o
  "oi, tudo bem" foi validado, não a tarefa agente longa de verdade.
  Valide com um `callout` simples primeiro antes de confiar nos padrões
  mais complexos.
- Se o agente tem Node/npx disponível no ambiente onde a run do
  OpenCode executa, e se os workarounds de `ambiente.md` (GSAP local,
  `HYPERFRAMES_BROWSER_PATH`, fallback de fontes) são necessários
  também nesse contexto — o teste que fizemos não envolveu nenhum
  comando `npx hyperframes`.
- A sincronização do filtro `overlay` do FFmpeg com `-itsoffset` em
  `editor.py` — teste com um overlay real renderizado antes de confiar
  no resultado; ajuste se o vídeo final não estiver no tempo certo.
- Se o id do modelo (`openrouter/nvidia/nemotron-3-ultra-550b-a55b:free`)
  continua existindo — modelos `:free` no OpenRouter mudam/saem de linha
  com frequência; confirme no seletor de modelo do agente no Paperclip
  antes de rodar sem supervisão se já faz tempo desde o último teste.
