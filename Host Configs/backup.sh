#!/bin/bash
# ==========================================================
# Script Monynha — Backup XO + Limpeza + Serviço Coolify
# ==========================================================
# Uso:
#   sudo bash monynha-fix.sh
# ==========================================================

BACKUP_DIR="/root/xo-backups"
DATE=$(date +%Y%m%d-%H%M%S)
BACKUP_FILE="$BACKUP_DIR/xo-config-$DATE.json"

echo "📦 Fazendo backup do Xen Orchestra..."

# Criar pasta de backup
mkdir -p $BACKUP_DIR

# Tentar exportar config via xo-server-cli (se instalado)
if command -v xo-server >/dev/null 2>&1; then
  echo "⚡ Exportando config com xo-server..."
  xo-server --export-config > "$BACKUP_FILE"
else
  # fallback: copiar config.json atual se existir
  CONFIG_FILE="/home/xo/.config/xo-server/config.json"
  if [ -f "$CONFIG_FILE" ]; then
    echo "⚡ Copiando config.json atual..."
    cp "$CONFIG_FILE" "$BACKUP_FILE"
  else
    echo "⚠️ Nenhum arquivo de configuração encontrado para backup."
  fi
fi

echo "✅ Backup salvo em: $BACKUP_FILE"

# ==========================================================
echo "🚨 Parando e removendo Xen Orchestra antigo..."

# Parar e remover serviço XO
systemctl stop xo-server 2>/dev/null
systemctl disable xo-server 2>/dev/null

rm -rf /opt/xo
rm -rf /opt/xo-builds
rm -rf /home/xo/.config/xo-server
rm -f /etc/systemd/system/xo-server.service

systemctl daemon-reload

echo "✅ Xen Orchestra removido com sucesso."

# ==========================================================
echo "⚙️ Criando serviço systemd para Coolify..."

# Cria diretório caso não exista
mkdir -p /data/coolify/source

cat <<EOF >/etc/systemd/system/coolify.service
[Unit]
Description=Coolify Service
Requires=docker.service
After=docker.service

[Service]
WorkingDirectory=/data/coolify/source
ExecStart=/usr/bin/docker compose up -d
ExecStop=/usr/bin/docker compose down
Restart=always
TimeoutStartSec=0

[Install]
WantedBy=multi-user.target
EOF

# Recarregar systemd e habilitar serviço
systemctl daemon-reload
systemctl enable coolify
systemctl start coolify

echo "✅ Serviço Coolify criado e habilitado."
echo "🔄 Coolify subirá automaticamente em cada reboot."

# ==========================================================
echo "🎉 Script concluído!"
echo "   - Backup XO: $BACKUP_FILE"
echo "   - Para reinstalar XO: cd ~/XenOrchestraInstallerUpdater && sudo ./xo-install.sh --install"
