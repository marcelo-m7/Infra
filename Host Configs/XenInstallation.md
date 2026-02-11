# 🏗️ Guia de Instalação e Configuração — Xen Orchestra @ infra.monynha.com

Este documento descreve o processo de provisionamento e configuração do servidor **Xen Orchestra (XO)** no **Hetzner**, utilizando **Debian 11 minimal** como sistema operacional base.

---

## 📌 Visão Geral

* **Servidor**: Hetzner Cloud (KVM dedicado ao Xen Orchestra)
* **SO**: Debian 11 minimal
* **Aplicação**: [Xen Orchestra (XO)](https://xen-orchestra.com/) via [XenOrchestraInstallerUpdater](https://github.com/ronivay/XenOrchestraInstallerUpdater)
* **Domínio público**: `infra.monynha.com`
* **Segurança**: HTTPS válido via Let’s Encrypt (ACME)
* **Usuário dedicado**: `xo`

---

## ⚙️ 1. Preparação do servidor

### Acessar via SSH

```bash
ssh root@<IP_DO_SERVIDOR>
```

### Atualizar sistema

```bash
apt update && apt upgrade -y
apt install -y curl wget git sudo
```

### Criar usuário dedicado

```bash
adduser xo
usermod -aG sudo xo
```

---

## 🔧 2. Configuração do Firewall

> Obs: no Hetzner o firewall local não vem ativo por padrão.
> Se for necessário, liberar manualmente com iptables:

```bash
iptables -A INPUT -p tcp --dport 80 -j ACCEPT
iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

---

## 💾 3. Swap (caso < 3 GB RAM)

Se o servidor tiver menos de 3 GB de RAM, criar swap de 2 GB para evitar falhas no build:

```bash
sudo fallocate -l 2G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

Adicionar no `/etc/fstab` para persistência (faça isso como root ou usando sudo). NÃO tente rodar a linha abaixo como comando — ela é uma entrada de arquivo e deve ser escrita em `/etc/fstab`:

```bash
# Recommended (safe, appends the line to /etc/fstab using sudo)
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Alternatively (use a root shell to redirect safely):
sudo bash -c 'printf "%s\n" "/swapfile none swap sw 0 0" >> /etc/fstab'
```

Verifique se a swap está ativa e listada:

```bash
sudo swapon --show    # mostra swaps ativas
free -h               # mostra memória + swap
```

Se você acidentalmente adicionou a mesma linha mais de uma vez (por exemplo, duas entradas idênticas em `/etc/fstab`), remova entradas duplicadas com cuidado. Opções seguras:

```bash
# 1) Editar manualmente (safe & simple)
sudo nano /etc/fstab

# 2) Remove duplicatas não interativamente (creates a temp file then replaces fstab)
sudo awk '!seen[$0]++' /etc/fstab | sudo tee /etc/fstab.tmp && sudo mv /etc/fstab.tmp /etc/fstab

# After fixing /etc/fstab, re-enable swap entries from fstab
sudo swapon -a
sudo swapon --show
```

Nota: `mount -a` tentará montar todas as entradas em `/etc/fstab`; use com cuidado se houver linhas potencialmente incorretas.

---

## 📥 4. Instalação do Xen Orchestra

### Clonar o instalador

```bash
git clone https://github.com/ronivay/XenOrchestraInstallerUpdater.git
cd XenOrchestraInstallerUpdater
cp sample.xo-install.cfg xo-install.cfg
```

### Configurar `xo-install.cfg`

Arquivo ajustado:

```bash
# Usuário que vai rodar o serviço
XOUSER="xo"

# Permitir uso de sudo
USESUDO="true"
GENSUDO="true"

# Porta HTTPS
PORT="443"

# Diretório de instalação
INSTALLDIR="/opt/xo"

# Atualizações automáticas
SELFUPGRADE="true"
CONFIGUPDATE="true"

# Repositório oficial
REPOSITORY="https://github.com/vatesfr/xen-orchestra"
BRANCH="master"

# Plugins
PLUGINS="all"

# Atualizações de Node/Yarn
AUTOUPDATE="true"

# Checks
OS_CHECK="true"
ARCH_CHECK="true"

# Rollbacks
PRESERVE="3"

##############################################
# Let's Encrypt / HTTPS
##############################################

# Ativar ACME (Let's Encrypt)
ACME="true"

# Domínio público
ACME_DOMAIN="infra.monynha.com"

# Email para notificações
ACME_EMAIL="infra@monynha.com"

# Usar Let's Encrypt production
ACME_CA="letsencrypt/production"
```

### Rodar instalação

```bash
sudo ./xo-install.sh --install
```

---

## 🌐 5. Acesso ao Xen Orchestra

Após a instalação, acessar:

```text
https://infra.monynha.com
```

Login inicial:

```text
[email protected] / admin
```

Troque a senha imediatamente.

---

## 🔒 6. Pós-instalação

1. **Trocar senha padrão** do admin.
2. **Adicionar hosts** XCP-ng / XenServer em **Settings → Remote**.
3. **Testar certificados HTTPS** (`certbot` via ACME).
4. Configurar **backups/snapshots**.
5. Ativar **rollback automático** via `PRESERVE`.
6. (Opcional) Instalar proxy:

   ```bash
   sudo ./xo-install.sh --install --proxy
   ```

---

## 🔄 7. Manutenção

### Atualizar XO

```bash
cd ~/XenOrchestraInstallerUpdater
sudo ./xo-install.sh --update
```

### Rollback em caso de falha

```bash
sudo ./xo-install.sh --rollback
```

---

## 📂 Estrutura de diretórios

* Instalador: `~/XenOrchestraInstallerUpdater`
* Código XO: `/opt/xo`
* Builds: `/opt/xo/xo-builds`
* Config: `/home/xo/.config/xo-server/config.toml`
* Certificados SSL: `/etc/letsencrypt/live/infra.monynha.com/`

---

## ✅ Resumo

* Debian 11 minimal configurado no Hetzner
* Usuário `xo` dedicado
* Firewall liberando portas 80/443
* Swap criado para builds
* XO instalado via `XenOrchestraInstallerUpdater`
* HTTPS ativo via Let’s Encrypt em `infra.monynha.com`
* Ambiente pronto para gerenciar hosts XCP-ng / XenServer

---

✨ **Monynha Softwares — Infraestrutura com orgulho, diversidade e resistência.**
🚀 Agora o **infra.monynha.com** é a central de orquestração da sua nuvem!
