# Integração com o pipeline do canal dark

Como os 5 padrões entram no pipeline Curador → Roteirista → **Editor**
→ Revisor → Saída, em duas etapas separadas:

```
roteiros.json (Roteirista, com overlays opcionais)
        |
pipeline/gerar_overlays.py   <- ETAPA COM IA: despacha o Dev (OpenCode
        |                        + modelo grátis via OpenRouter) pra
        v                        montar+renderizar cada overlay via esta skill
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

**Por que Dev (OpenCode + modelo grátis) e não Tech Lead (Claude Code):**
esta etapa roda sem supervisão, potencialmente várias vezes por vídeo —
é exatamente o tipo de trabalho repetitivo que o seu setup já reserva
pro Dev, pra manter o canal "tudo grátis" (ver README) e não gastar a
assinatura do Claude à toa. `gerar_overlays.py` usa `--agent opencode`
por padrão, com o modelo `openrouter/nvidia/nemotron-3-ultra-550b-a55b:free`
— o provider `openrouter` já vem embutido no OpenCode (sem precisar de
ZenMux, Kimi Code ou qualquer conta/chave separada; só `opencode auth
login`). `--modelo-reserva` cai pro `nemotron-3-super-120b-a12b:free`
(mais rápido/menor) se o modelo padrão falhar ou travar. O Tech Lead
fica reservado pra prototipagem manual (como os 5 padrões foram
validados nesta sessão) ou correção pontual — dá pra forçar com
`--agent claude` num overlay específico se o Dev não acertar.

(Nota histórica: cogitamos primeiro Kimi K3 via ZenMux e depois o Kimi
Code CLI nativo — mas Kimi Code exige assinatura paga da Moonshot, e o
Kimi K3 "grátis" documentado no README original não ficou confirmado
contra a doc oficial do ZenMux. Os modelos `:free` do OpenRouter, já
embutidos no OpenCode sem nenhum cadastro extra, são o caminho mais
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
  agente (Dev por padrão) usa isso pra substituir o texto de exemplo de
  cada referência pelo conteúdo real, mantendo a estrutura/timing/paleta.

## Contrato de conteúdo por padrão (o que o Roteirista deve preencher)

| Padrão | Campos de `conteudo` | Prontidão pra geração automática |
| --- | --- | --- |
| `callout` | `rotulo` (sigla curta), `frase` (texto de destaque) | **Alta** — só texto, estrutura genérica |
| `recorte` | `letra` (1-2 caracteres/palavra curta pra forma monumental) | **Média** — a letra é fácil de trocar; multidão/chão são decorativos fixos |
| `ritmo` | `descricao` (o que as duas "silhuetas" representam) — **não gera imagens reais**, usa formas placeholder | **Baixa pra conteúdo real** — pra usar com imagens/fotos de verdade precisa passar por `/media-use` antes (sourcing de imagem), isso ainda não está encadeado aqui |
| `territorio` | `eventos`: lista de `{nome, ano, descricao}` — mas as posições/formas no mapa são desenhadas à mão (coordenadas de pixel) pro caso específico de expansão territorial dos EUA | **Baixa** — é um protótipo ilustrativo de UM caso específico, não um gerador genérico de "qualquer mapa, qualquer território"; adaptar pra outro mapa/assunto exige o Tech Lead redesenhar as formas, não só trocar texto |
| `janela` | `evento_nome`, `evento_tempo`, `reacao_descricao` (o que muda no mapa de fundo) | **Baixa** — mesmo caso do território: o mapa/país de fundo é um placeholder específico (URSS), não genérico |

**Na prática hoje:** `callout` e `recorte` são os mais seguros pra
automação sem supervisão com um modelo mais fraco (Nemotron 3 Ultra).
`ritmo`,
`territorio` e `janela` tendem a precisar de revisão humana do
resultado (ou de mais trabalho de design) antes de confiar neles em
produção, porque o conteúdo de exemplo validado era bem específico — o
agente vai ter que *adaptar* a estrutura visual pro assunto real, não só
preencher campos. Se o Dev travar muito num desses três, vale rodar
aquele overlay específico com `--agent claude` (Tech Lead) em vez de
abrir mão do padrão.

## Scripts

- `pipeline/gerar_overlays.py` — lê `roteiros.json`, despacha um agente
  (Dev/OpenCode + Nemotron 3 Ultra grátis via OpenRouter por padrão,
  Tech Lead/Claude Code opcional via `--agent claude`) em modo headless
  por overlay, com o conteúdo + a referência desta skill, grava os mp4s
  e escreve `roteiros.overlays.json` com `overlays[i]["arquivo"]`
  preenchido.
- `pipeline/editor.py` — o Editor original + composição: se um roteiro
  tem `overlays` com `"arquivo"` preenchido, substitui o trecho
  correspondente do corte final pelo mp4 do overlay (via filtro
  `overlay` do FFmpeg, mantendo o áudio original).

## O que já foi confirmado, e o que ainda não

**Confirmado:** `opencode run --model openrouter/nvidia/nemotron-3-ultra-550b-a55b:free "<prompt>"`
funciona e responde corretamente — testado manualmente no servidor.

**Ainda não testado de ponta a ponta:**
- O fluxo completo (ler os 4 arquivos de referência da skill, montar a
  composição GSAP, rodar `hyperframes check`/`snapshot`/`render`,
  corrigir um erro de lint sozinho) com esse modelo — só o "oi, tudo
  bem" foi validado, não a tarefa agente longa de verdade. Valide com
  um `callout` simples primeiro antes de confiar nos padrões mais
  complexos.
- A sincronização do filtro `overlay` do FFmpeg com `-itsoffset` — teste
  com um overlay real renderizado antes de confiar no resultado; ajuste
  se o vídeo final não estiver no tempo certo.
- Se o id do modelo (`openrouter/nvidia/nemotron-3-ultra-550b-a55b:free`)
  continua existindo — modelos `:free` no OpenRouter mudam/saem de linha
  com frequência; confirme com `opencode models openrouter` antes de
  rodar sem supervisão se já faz tempo desde o último teste.
