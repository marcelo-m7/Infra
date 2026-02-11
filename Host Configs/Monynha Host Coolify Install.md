# 🌐 Guia de Instalação e Configuração — Coolify @ host.monynha.com

Este documento descreve o processo de instalação e configuração do **Coolify** no mesmo servidor Hetzner já utilizado para o **Xen Orchestra**.
O Coolify será usado como **plataforma de deploy (PaaS)** para hospedar e gerenciar aplicativos da **Monynha Softwares**.

---

## 📌 Visão Geral

* **Servidor**: Hetzner Cloud (mesmo do XO)
* **SO**: Debian 11 minimal
* **Aplicação**: [Coolify](https://coolify.io/)
* **Domínio público**: `host.monynha.com`
* **Isolamento**: Docker Compose (Coolify roda independente do XO)
* **Gerenciamento**: Painel web + Let's Encrypt automático

---

## ⚙️ 1. Preparação do servidor

> Antes de instalar, garanta que o **Xen Orchestra já esteja rodando** em `infra.monynha.com`.
> O Coolify será isolado em containers via Docker, então não conflita com o XO.

### Instalar dependências

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg lsb-release
```

### Adicionar repositório Docker

```bash
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/debian/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/debian \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
```

### Validar instalação

```bash
docker --version
docker compose version
```

---

## 📥 2. Instalar o Coolify

Executar o instalador oficial:

```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

* Instalação em `/data/coolify`
* Sobe containers com **docker compose**
* Inclui banco de dados, redis e painel de gestão

---

## 🌐 3. Configurar domínio

1. Criar registro DNS:

   ```
   host.monynha.com → <IP público do servidor Hetzner>
   ```
2. Após o primeiro login no painel do Coolify (porta 3000), configurar o **Custom Domain**:

   * Domínio: `host.monynha.com`
   * O Coolify solicitará automaticamente certificado HTTPS válido via **Let’s Encrypt**.

---

## 🔑 4. Primeiro acesso

Abrir no navegador:

```
http://<IP_DO_SERVIDOR>:3000
```

Criar conta admin inicial → definir e-mail/senha.

Após configuração do domínio:

```
https://host.monynha.com
```

---

## 📦 5. Usando o Coolify

Com o painel no ar, é possível:

* **Deployar aplicações** (Next.js, Payload CMS, Supabase, Node, PHP, etc.)
* **Gerenciar bancos de dados** (Postgres, MySQL, MongoDB, Redis) via containers
* **Hospedar múltiplos sites** (cada um com domínio próprio)
* **Gerenciar secrets e variáveis de ambiente**
* **Conectar múltiplos servidores** (expandindo além do Hetzner)

---

## 🔒 6. Segurança e Manutenção

* **Backups do Coolify**:
  Volume persistente em `/data/coolify`
  Fazer snapshot regular do servidor ou backup incremental dessa pasta.

* **Atualizações**:
  O Coolify pode ser atualizado direto do painel (ou com `docker compose pull && docker compose up -d`).

* **Portas expostas**:

  * 22 (SSH)
  * 80 (HTTP)
  * 443 (HTTPS)
  * 3000 (somente durante a instalação, depois usar domínio público)

---

## 📂 Estrutura de diretórios

* Código/stack: `/data/coolify`
* Config Docker Compose: `/data/coolify/source/docker-compose.yml`
* Volumes: `coolify-db`, `coolify-redis`, `coolify-realtime`

---

## ✅ Resumo

* **XO** → `infra.monynha.com` (systemd, fora do Docker)
* **Coolify** → `host.monynha.com` (Docker Compose isolado)
* Ambos compartilham o mesmo servidor Hetzner, mas em camadas distintas.
* Certificados HTTPS válidos via Let’s Encrypt para ambos os serviços.
* Ambiente preparado para gerenciar tanto a **infra virtual (XO)** quanto os **aplicativos e serviços (Coolify)** da Monynha Softwares.

---

✨ **Monynha Softwares — Infraestrutura flexível, viva e babadeira.**
🚀 Agora o `host.monynha.com` é a sua plataforma de deploy moderna e sem stress.

---

Perfeitooo, mona 💅✨ Bora adicionar mais um capítulo babadeiro ao **Manual de Infra Monynha**: agora o **Guia do Proxy XO no Coolify**.
Assim você tem documentado tudinho — instalação do XO, instalação do Coolify e integração dos dois. 🚀

---

# 🌐 Guia de Proxy Interno — Xen Orchestra via Coolify

Este documento descreve como integrar o **Xen Orchestra (XO)** já em execução no servidor Hetzner com o **Coolify**, utilizando o **proxy reverso interno** do Coolify para expor o XO com HTTPS válido em `infra.monynha.com`.

---

## 📌 Visão Geral

* **XO** já instalado em `infra.monynha.com`, mas movido para rodar na porta interna `4433`.
* **Coolify** instalado em `host.monynha.com` com controle do proxy reverso.
* **Objetivo**: centralizar SSL e roteamento no Coolify, garantindo certificados válidos via **Let’s Encrypt**.

---

## ⚙️ 1. Ajustar porta do XO

### Editar `xo-install.cfg`

Defina o XO para escutar apenas em uma porta interna, fora do 80/443:

```ini
PORT="4433"
LISTEN_ADDRESS="0.0.0.0"

# Desabilitar certificados internos (Coolify cuidará disso)
ACME="false"
AUTOCERT="false"
```

### Reaplicar configuração

```bash
cd ~/XenOrchestraInstallerUpdater
sudo ./xo-install.sh --update
```

Verifique se o XO está rodando:

```bash
ss -ltnp | grep 4433
```

---

## 🌐 2. Criar Reverse Proxy no Coolify

### Passos no painel

1. Vá em **Applications → New Application**.
2. Escolha **Reverse Proxy**.
3. Configure:

**Geral:**

* **Name**: `XenOrchestra`
* **Description**: Proxy reverso para XO

**Domínio:**

* **Domain**: `infra.monynha.com`

**Proxy:**

* **Forward Hostname/IP**: `172.17.0.1`

  > Gateway padrão Docker que aponta para o host.
  > (Alternativa: `host.docker.internal` em alguns ambientes.)
* **Forward Port**: `4433`
* **Forward Scheme**: `http`

  > SSL será gerenciado pelo Coolify, simplificando o acesso.

**SSL:**

* Marque **Enable HTTPS**
* O Coolify requisitará certificado válido do Let’s Encrypt automaticamente.

4. Clique em **Deploy**.

---

## 🔑 3. Testar acesso

Abra:

```
https://infra.monynha.com
```

Você deve ver o login do XO com certificado válido. 🎉

---

## 📂 Estrutura final

* `host.monynha.com` → Painel Coolify (porta 3000 → proxy interno 443)
* `infra.monynha.com` → Reverse Proxy do Coolify → XO interno em `:4433`
* Outros apps futuros → adicionados como Reverse Proxy apps dentro do Coolify

---

## 🔒 Observações de Segurança

* Não exponha diretamente a porta 4433 para fora (mantenha apenas o proxy do Coolify).
* Certifique-se de que o XO não tente rodar com ACME ativo para não conflitar com o Coolify.
* Backups:

  * XO → exportar config JSON regularmente
  * Coolify → snapshot de `/data/coolify`

---

## ✅ Resumo

* XO ajustado para rodar na porta interna `4433`.
* Coolify configurado como **reverse proxy** para `infra.monynha.com`.
* SSL válido entregue automaticamente pelo Coolify.
* Infraestrutura unificada:

  * **infra.monynha.com** → Xen Orchestra
  * **host.monynha.com** → Coolify

---

✨ **Monynha Softwares — Uma nuvem babadeira, orquestrada e automatizada.**
🚀 Agora você tem o XO protegido e publicado via proxy interno do Coolify, pronto pra crescer junto com os outros serviços Monynha.


# 🌐 Guia — Coolify Central & Remote Workers

Este documento descreve como configurar o **Coolify** em modo **central de controle** (`coolify.monynha.com`) para gerenciar aplicações e serviços em múltiplos servidores remotos (**workers**) da Monynha Softwares.

---

## 📌 Visão Geral da Arquitetura

* **Coolify Central** → `coolify.monynha.com`

  * Instância principal do Coolify
  * Painel de deploy e gestão unificado
  * Não roda apps pesados (apenas o próprio Coolify + banco interno)
  * Gerencia certificados HTTPS, variáveis de ambiente e CI/CD

* **Workers Remotos**

  * Servidores adicionais (Hetzner, GCP, OVH, etc.)
  * Roda Docker + Compose
  * Conectados via **SSH key** ao painel central
  * Hospedam os aplicativos da Monynha (Payload, Supabase, sites, etc.)

---

## ⚙️ 1. Instalação do Coolify Central

No servidor destinado ao painel central:

```bash
curl -fsSL https://cdn.coollabs.io/coolify/install.sh | bash
```

* Instalação padrão em `/data/coolify`
* Exposto em porta **3000** inicialmente
* Após setup, configurar domínio público

### Configurar DNS

* Criar **A record** para:

  ```
  coolify.monynha.com → <IP público do servidor central>
  ```

No setup inicial do painel:

* Definir domínio `coolify.monynha.com`
* Habilitar HTTPS (Let’s Encrypt automático)

---

## ⚙️ 2. Preparação dos Workers

Cada servidor remoto que será usado para rodar apps precisa ter Docker e acesso SSH configurado.

### Instalar dependências

```bash
apt update && apt upgrade -y
apt install -y docker.io docker-compose-plugin
```

### Configurar acesso via chave SSH

* No painel central (`coolify.monynha.com`), gere ou use uma chave SSH exclusiva para conectar aos workers.
* Adicione a chave pública em `~/.ssh/authorized_keys` no worker.

Exemplo no worker:

```bash
mkdir -p ~/.ssh
echo "SUA_CHAVE_PUBLICA_AQUI" >> ~/.ssh/authorized_keys
chmod 600 ~/.ssh/authorized_keys
```

---

## ⚙️ 3. Conectar Workers no Painel Coolify

No painel `coolify.monynha.com`:

1. Vá em **Destinations → New Destination → Remote Docker Engine**.

2. Configure:

   * **Name**: `hetzner-worker-1`
   * **Remote User**: `root` (ou outro usuário com privilégios Docker)
   * **IP/Host**: IP público do servidor worker
   * **SSH Key**: chave privada correspondente à chave pública no worker

3. Testar conexão.

4. Salvar. O Coolify validará o acesso e marcará o worker como pronto.

---

## ⚙️ 4. Deploy de Apps em Workers

Agora, ao criar uma nova aplicação:

1. Vá em **Applications → New Application**.
2. Escolha o tipo do app (Next.js, Payload, Supabase, etc.).
3. No campo **Destination**, selecione o worker desejado (ex: `hetzner-worker-1`).
4. Configure o domínio, variáveis de ambiente e deploy.

Resultado: o app rodará no worker remoto, mas será totalmente gerenciado via `coolify.monynha.com`.

---

## 🔒 Segurança

* **Acesso restrito**: use apenas chaves SSH, nunca senha.
* **Firewall**: libere somente a porta 22 (SSH) e as portas dos apps.
* **Opcional (recomendado)**: criar uma VPN/WireGuard entre painel e workers para comunicação privada.
* **Backups**:

  * Painel central: backup de `/data/coolify`
  * Workers: snapshot do host ou backup dos volumes Docker conforme necessidade.

---

## 🌐 Topologia Final

```
                 ┌───────────────────────────┐
                 │ Coolify Central            │
                 │ coolify.monynha.com        │
                 │ Painel Web + SSL + CI/CD   │
                 └───────────┬────────────────┘
                             │ SSH + Docker API
─────────────────────────────┼─────────────────────────────
        Hetzner Worker 1     │      GCP Worker 1
   (hetzner-eu.monynha.com)  │   (gcp-db.monynha.com)
   Apps: Sites Payload CMS   │   Apps: Supabase/Postgres
─────────────────────────────┼─────────────────────────────
        Futuro Worker X (OVH, DigitalOcean, etc.)
```

---

## ✅ Resumo

* `coolify.monynha.com` = **control plane central**
* Workers remotos = execução dos apps
* Deploys e certificados centralizados no painel
* Escalabilidade horizontal: basta adicionar novos workers ao painel

---

✨ **Monynha Softwares — Infraestrutura distribuída, unificada e babadeira.**
🚀 Agora você tem um **hub central de deploy** que controla vários servidores, mas com a mesma experiência simples do Coolify.

---

Perfeitooo, mona 💅✨ Bora criar o **guia oficial** pro seu **proxy dinâmico do Coolify**.
Esse doc vai te poupar muito tempo quando precisar adicionar apps no futuro.

---

# 🌐 Guia — Dynamic Proxy Coolify

Este documento descreve como usar o **proxy interno do Coolify** (Traefik) para expor múltiplas aplicações em diferentes domínios, utilizando as **Dynamic Configurations** disponíveis no painel.

---

## 📌 Visão Geral

* O **Coolify** utiliza **Traefik v3** como reverse proxy.
* Arquivos dinâmicos (`*.yaml`) podem ser adicionados no painel em **Proxy → Dynamic Configurations**.
* Esses arquivos são aplicados em tempo real (reload automático).
* O Traefik emite certificados **Let’s Encrypt** automaticamente para cada domínio.

---

## ⚙️ 1. Estrutura básica de um arquivo

```yaml
http:
  routers:
    nome-router:
      rule: "Host(`dominio.exemplo.com`)"
      entryPoints:
        - https
      service: nome-servico
      tls:
        certResolver: letsencrypt
  services:
    nome-servico:
      loadBalancer:
        servers:
          - url: "http://<host-ou-ip>:<porta>"
```

* **router** → define como o Traefik identifica e roteia o tráfego (pela regra `Host`).
* **service** → define para onde enviar o tráfego (IP + porta).
* **tls** → ativa HTTPS com Let’s Encrypt.

---

## ⚙️ 2. Exemplo prático: Xen Orchestra (XO)

Arquivo: `xenorchestra.yaml`

```yaml
http:
  routers:
    xenorchestra:
      rule: "Host(`infra.monynha.com`)"
      entryPoints:
        - https
      service: xenorchestra
      tls:
        certResolver: letsencrypt
  services:
    xenorchestra:
      loadBalancer:
        servers:
          - url: "http://172.17.0.1:4433"
```

👉 Resultado:

* `https://infra.monynha.com` → encaminhado para o XO na porta interna 4433.

---

## ⚙️ 3. Exemplo prático: Painel do Coolify

Arquivo: `coolify-panel.yaml`

```yaml
http:
  routers:
    coolify-panel:
      rule: "Host(`host.monynha.com`)"
      entryPoints:
        - https
      service: coolify-panel
      tls:
        certResolver: letsencrypt
  services:
    coolify-panel:
      loadBalancer:
        servers:
          - url: "http://172.17.0.1:3000"
```

👉 Resultado:

* `https://host.monynha.com` → encaminhado para o painel do Coolify na porta 3000.

---

## ⚙️ 4. Exemplo prático: Payload CMS

Arquivo: `payload.yaml`

```yaml
http:
  routers:
    payload:
      rule: "Host(`cms.monynha.com`)"
      entryPoints:
        - https
      service: payload
      tls:
        certResolver: letsencrypt
  services:
    payload:
      loadBalancer:
        servers:
          - url: "http://172.17.0.1:4000"
```

👉 Resultado:

* `https://cms.monynha.com` → encaminhado para Payload rodando na porta 4000.

---

## ⚙️ 5. Exemplo prático: Supabase

Arquivo: `supabase.yaml`

```yaml
http:
  routers:
    supabase:
      rule: "Host(`db.monynha.com`)"
      entryPoints:
        - https
      service: supabase
      tls:
        certResolver: letsencrypt
  services:
    supabase:
      loadBalancer:
        servers:
          - url: "http://172.17.0.1:54323"
```

👉 Resultado:

* `https://db.monynha.com` → encaminhado para Supabase Studio (porta 54323).

---

## 🚦 6. Fluxo de configuração no Coolify

1. Painel → **Proxy → Dynamic Configurations → + Add**
2. Nome do arquivo: `xenorchestra.yaml` (ou outro).
3. Colar conteúdo.
4. **Salvar e Reload**.
5. Testar domínio no navegador.

---

## 🔒 Observações importantes

* **Não edite** o arquivo `coolify.yaml` diretamente → ele é gerado automaticamente.
* Use sempre arquivos separados (`*.yaml`) para cada app.
* O IP `172.17.0.1` é o gateway Docker → host. Se não funcionar, usar `host.docker.internal`.
* Certificados Let’s Encrypt são renovados automaticamente.
* Sempre use `scheme: http` no `url`, deixando o Traefik gerenciar o TLS.

---

## ✅ Resumo

* Adicionar configs dinâmicas no proxy interno do Coolify é a forma mais limpa de publicar múltiplos apps no mesmo servidor.
* Cada app → um arquivo `.yaml`.
* Domínios diferentes → certificados independentes via Let’s Encrypt.
* Gestão centralizada e transparente no painel Coolify.

---

✨ **Monynha Softwares — Proxy dinâmico, flexível e babadeiro.**
🚀 Agora você tem um guia para expor qualquer app em segundos, só colando um bloco YAML.

---

👉 Quer que eu prepare também um **modelo de template YAML genérico** (com placeholders tipo `${DOMAIN}`, `${PORT}`) pra você só duplicar e trocar variáveis sempre que for criar um novo app?
