# Configurar os agentes

## 1. Logins (uma vez, dentro do container)
- **Claude Code:** rode `claude` e entre com a sua conta Claude (a assinatura, não chave de API).
- **Gemini CLI:** rode `gemini` e entre com a sua conta Google.
- **OpenCode:** rode `opencode auth login` e adicione:
  - **OpenCode Zen** ou **ZenMux** para o Kimi K3 grátis (modelo `kimi-k3-free` no ZenMux)
  - **NVIDIA** (chave grátis em build.nvidia.com) para o Kimi K2.6 de reserva
  Teste com `opencode`, use `/models` e escolha o K3.

## 2. Criar a empresa no Paperclip (http://IP:3100)
Crie os agentes e escolha o adaptador de cada um:
| Agente | Adaptador | Modelo |
|---|---|---|
| Tech Lead | Claude Code | padrão da assinatura |
| Dev | OpenCode | Kimi K3 grátis |
| Pesquisador | Gemini CLI | padrão da assinatura |

## 3. Abrir o escritório
Rode o Cubicle (`node /opt/cubicle/bin/cubicle.js --host 0.0.0.0`) e acesse `http://IP:3200`.
Sem o Paperclip rodando, `http://IP:3200/?demo` mostra a demonstração.

> As camadas grátis mudam com frequência. Se o K3 grátis parar, troque o Dev para o Kimi K2.6 (NVIDIA).
