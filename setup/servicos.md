# Deixar tudo ligando sozinho

Rode como **root** no container (saia do usuário cubicle com `exit`):

```bash
cd ~/cubicle-local && git pull
cp services/paperclip.service services/cubicle.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now paperclip cubicle
systemctl status paperclip cubicle --no-pager
```

- Paperclip: http://192.168.0.74:3100
- Cubicle (escritório): http://192.168.0.74:3200

## Chave do Paperclip para o Cubicle
Como o Paperclip está em modo autenticado, o Cubicle precisa de uma chave de API (de preferência só leitura) criada no painel do Paperclip:

```bash
echo 'PAPERCLIP_TOKEN=cole-a-chave-aqui' > /home/cubicle/.cubicle.env
chown cubicle:cubicle /home/cubicle/.cubicle.env && chmod 600 /home/cubicle/.cubicle.env
systemctl restart cubicle
```

Logs: `journalctl -u paperclip -f` ou `journalctl -u cubicle -f`
