#!/usr/bin/env bash
echo "== Uptime/carga ==";  uptime
echo "== Memória ==";       free -h
echo "== Disco ==";         df -h /
echo "== Serviços com falha =="; systemctl --failed --no-legend 2>/dev/null || echo "(systemctl indisponível)"
