---
name: resumo-do-servidor
description: Gera um resumo da saúde do servidor (CPU, memória, disco, serviços). Use quando pedirem status, saúde ou uso do servidor.
---

# Resumo do servidor

1. Rode `bash scripts/coletar.sh` nesta pasta.
2. Com a saída, escreva em português um resumo de até 5 linhas:
   - uso de CPU, memória e disco, com alerta se algo passar de 85%
   - serviços que estão parados
3. Termine com uma recomendação, se houver algo a fazer.
