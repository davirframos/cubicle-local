# Integração com o pipeline do canal dark

Como os 5 padrões entram no pipeline Curador → Roteirista → **Editor**
→ Revisor → Saída, em duas etapas separadas:

```
roteiros.json (Roteirista, com overlays opcionais)
        |
pipeline/gerar_overlays.py   <- ETAPA COM IA: despacha o Tech Lead
        |                        (Claude Code) pra montar+renderizar
        v                        cada overlay via esta skill
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
  Tech Lead usa isso pra substituir o texto de exemplo de cada
  referência pelo conteúdo real, mantendo a estrutura/timing/paleta.

## Contrato de conteúdo por padrão (o que o Roteirista deve preencher)

| Padrão | Campos de `conteudo` | Prontidão pra geração automática |
| --- | --- | --- |
| `callout` | `rotulo` (sigla curta), `frase` (texto de destaque) | **Alta** — só texto, estrutura genérica |
| `recorte` | `letra` (1-2 caracteres/palavra curta pra forma monumental) | **Média** — a letra é fácil de trocar; multidão/chão são decorativos fixos |
| `ritmo` | `descricao` (o que as duas "silhuetas" representam) — **não gera imagens reais**, usa formas placeholder | **Baixa pra conteúdo real** — pra usar com imagens/fotos de verdade precisa passar por `/media-use` antes (sourcing de imagem), isso ainda não está encadeado aqui |
| `territorio` | `eventos`: lista de `{nome, ano, descricao}` — mas as posições/formas no mapa são desenhadas à mão (coordenadas de pixel) pro caso específico de expansão territorial dos EUA | **Baixa** — é um protótipo ilustrativo de UM caso específico, não um gerador genérico de "qualquer mapa, qualquer território"; adaptar pra outro mapa/assunto exige o Tech Lead redesenhar as formas, não só trocar texto |
| `janela` | `evento_nome`, `evento_tempo`, `reacao_descricao` (o que muda no mapa de fundo) | **Baixa** — mesmo caso do território: o mapa/país de fundo é um placeholder específico (URSS), não genérico |

**Na prática hoje:** `callout` e `recorte` são seguros pra automação via
`gerar_overlays.py` sem supervisão. `ritmo`, `territorio` e `janela`
tendem a precisar de revisão humana do resultado (ou de mais trabalho de
design) antes de confiar neles em produção, porque o conteúdo de
exemplo validado era bem específico — o Tech Lead vai ter que *adaptar*
a estrutura visual pro assunto real, não só preencher campos.

## Scripts

- `pipeline/gerar_overlays.py` — lê `roteiros.json`, despacha o Tech
  Lead (`claude -p`, modo headless) por overlay com o conteúdo + a
  referência desta skill, grava os mp4s e escreve
  `roteiros.overlays.json` com `overlays[i]["arquivo"]` preenchido.
- `pipeline/editor.py` — o Editor original + composição: se um roteiro
  tem `overlays` com `"arquivo"` preenchido, substitui o trecho
  correspondente do corte final pelo mp4 do overlay (via filtro
  `overlay` do FFmpeg, mantendo o áudio original).

## O que ainda não foi testado de ponta a ponta

- A chamada `claude -p "<prompt>"` em modo headless/não-interativo —
  confirme a sintaxe exata contra a versão do Claude Code CLI instalada
  no servidor (`claude --help`) antes de rodar em produção.
- A sincronização do filtro `overlay` do FFmpeg com `-itsoffset` — teste
  com um overlay real renderizado antes de confiar no resultado; ajuste
  se o vídeo final não estiver no tempo certo.
