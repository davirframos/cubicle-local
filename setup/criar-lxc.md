# Criar o container no Proxmox

1. Baixe o template: **local (proxmox) > CT Templates > Templates** e escolha `debian-13-standard` (ou 12).
2. Clique em **Create CT** (canto superior direito):
   - **Hostname:** `cubicle`
   - **Senha:** escolha uma
   - **Template:** o Debian que você baixou
   - **Disco:** 16 GB
   - **CPU:** 2 núcleos
   - **Memória:** 3072 MB, swap de 1024 MB
   - **Rede:** DHCP (ou um IP fixo da sua rede)
3. Marque **Start after created**.
4. Abra o **Console** do container, entre como `root` e rode:

```bash
apt update && apt install -y git
git clone https://github.com/davirframos/cubicle-local.git
cd cubicle-local && bash scripts/install.sh
```
