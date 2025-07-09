# Zabbix Agent RCE Exploit

## Descrição

Este é um POC (Proof of Concept) que demonstra a exploração de execução remota de código (RCE) em agentes Zabbix. O script utiliza a API JSON-RPC do Zabbix para listar hosts disponíveis e implantar shells reversas em sistemas Windows e Linux.

## ⚠️ Aviso Legal

Esta ferramenta foi desenvolvida APENAS para fins educacionais e de testes de segurança autorizados. O uso desta ferramenta sem autorização explícita pode violar leis e políticas de segurança. O autor não se responsabiliza pelo uso indevido ou ilegal desta ferramenta.

## Características

- Exploração de execução remota de código em agentes Zabbix
- Suporte para sistemas Windows e Linux
- Interface interativa para seleção de hosts e interfaces
- Detecção automática de sistema operacional
- Servidor HTTP integrado para servir payloads
- Sistema de logging completo
- Configuração via variáveis de ambiente (.env)

## Requisitos

- Python 3.6+
- Bibliotecas Python (ver requirements.txt)
- Acesso administrativo à API do Zabbix
- Token de API válido

## Instalação

1. Clone o repositório:
```bash
git clone https://github.com/ticofookfook/RCE_IN_AGENT_ZABBIX
cd RCE_IN_AGENT_ZABBIX
```

2. Instale as dependências:
```bash
pip3 install -r requirements.txt
```

3. Configure o arquivo `.env` com suas credenciais:
```bash
cp .env.example .env
# Edite o arquivo .env com suas configurações
```

## Configuração

Edite o arquivo `.env` com as seguintes configurações:

```
# Configurações do Zabbix
ZABBIX_URL=http://seu-servidor-zabbix/api_jsonrpc.php
AUTH_TOKEN=seu-token-de-api-zabbix

# Configurações do servidor de callback
IP_SHELL=seu-ip-publico-ou-vpn
PORT_SERVER_PYTHON=9000
```

## Uso

Execute o script principal:

```bash
python zabbix_rce.py
```

Opções de linha de comando:
- `--verbose` ou `-v`: Ativa o modo verboso com mais informações de debug
- `--port` ou `-p`: Define a porta para o servidor HTTP (sobrepõe a configuração no .env)

## Fluxo de Execução

1. O script lista todos os hosts disponíveis no servidor Zabbix
2. Você seleciona um host e uma interface para exploração
3. O script tenta detectar automaticamente o sistema operacional
4. Você confirma o tipo de sistema e fornece uma porta para a conexão reversa
5. O script implanta um item no Zabbix que executa uma shell reversa
6. Você precisa executar `nc -lvnp [porta]` na sua máquina para receber a conexão

## Limpeza

Para remover os itens implantados:
1. Acesse a interface web do Zabbix
2. Navegue até Configuration > Hosts > [Host] > Items
3. Encontre e exclua os itens "nc_reverse_shell" ou "powershell_reverse_shell"

## Logs

Os logs são salvos em `zabbix_rce.log` e também exibidos no console.

## Contribuições

Contribuições são bem-vindas! Por favor, abra um issue para discutir alterações propostas ou envie um pull request.

## Licença

Este projeto está licenciado sob a licença MIT - veja o arquivo LICENSE para detalhes.
