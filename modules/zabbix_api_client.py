"""
Cliente para API do Zabbix
Gerencia todas as operações de comunicação com a API do Zabbix
"""

import json
import requests
import logging
from typing import Dict, List, Optional, Any


class ZabbixAPIClient:
    """Cliente para interação com a API do Zabbix"""
    
    def __init__(self, url: str, auth_token: str, timeout: int = 10):
        self.url = url
        self.auth_token = auth_token
        self.timeout = timeout
        self.headers = {'Content-Type': 'application/json'}
        self.logger = logging.getLogger('zabbix_rce.api')
        
        # Contador para IDs únicos de requisições
        self._request_id = 1
    
    def _get_next_id(self) -> int:
        """Retorna próximo ID único para requisição"""
        current_id = self._request_id
        self._request_id += 1
        return current_id
    
    def _make_request(self, method: str, params: Dict) -> Optional[Dict]:
        """
        Faz uma requisição genérica para a API do Zabbix
        
        Args:
            method: Método da API (ex: 'host.get')
            params: Parâmetros do método
            
        Returns:
            Dict com a resposta ou None em caso de erro
        """
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "auth": self.auth_token,
            "id": self._get_next_id()
        }
        
        try:
            self.logger.debug(f"Fazendo requisição para {method}")
            response = requests.post(
                self.url, 
                headers=self.headers, 
                data=json.dumps(payload), 
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                self.logger.error(f"Erro HTTP {response.status_code}: {response.text}")
                return None
            
            response_data = response.json()
            
            if "error" in response_data:
                self.logger.error(f"Erro da API: {response_data['error']}")
                return None
            
            if "result" not in response_data:
                self.logger.error(f"Resposta inválida: {response_data}")
                return None
            
            return response_data
            
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro de conexão: {e}")
            return None
        except json.JSONDecodeError as e:
            self.logger.error(f"Erro ao decodificar JSON: {e}")
            return None
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            return None
    
    def test_connection(self) -> bool:
        """
        Testa a conexão com a API do Zabbix
        
        Returns:
            bool: True se a conexão está funcionando
        """
        self.logger.info("Testando conexão com a API do Zabbix...")
        
        # apiinfo.version NAO precisa de auth - esse era o erro!
        payload = {
            "jsonrpc": "2.0",
            "method": "apiinfo.version",
            "params": {},
            "id": 1
        }
        
        try:
            response = requests.post(
                self.url, 
                headers=self.headers, 
                data=json.dumps(payload), 
                timeout=self.timeout
            )
            
            if response.status_code != 200:
                self.logger.error(f"Erro HTTP {response.status_code}: {response.text}")
                return False
            
            response_data = response.json()
            
            if "error" in response_data:
                self.logger.error(f"Erro da API: {response_data['error']}")
                return False
            
            if "result" in response_data:
                version = response_data['result']
                self.logger.info(f"Conectado ao Zabbix versão: {version}")
                return True
            else:
                self.logger.error(f"Resposta inválida: {response_data}")
                return False
                
        except requests.exceptions.RequestException as e:
            self.logger.error(f"Erro de conexão: {e}")
            return False
        except json.JSONDecodeError as e:
            self.logger.error(f"Erro ao decodificar JSON: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Erro inesperado: {e}")
            return False
    
    def get_hosts(self) -> Optional[List[Dict]]:
        """
        Lista todos os hosts disponíveis
        
        Returns:
            List de dicts com informações dos hosts
        """
        self.logger.info("Buscando lista de hosts...")
        
        params = {
            "output": ["hostid", "host", "name", "status"],
            "selectInterfaces": [
                "interfaceid", "ip", "dns", "port", "type", "main"
            ],
            "selectGroups": ["groupid", "name"]
        }
        
        response = self._make_request("host.get", params)
        
        if response:
            hosts = response['result']
            self.logger.info(f"Encontrados {len(hosts)} hosts")
            return hosts
        
        return None
    
    def get_host_by_id(self, hostid: str) -> Optional[Dict]:
        """
        Busca um host específico por ID
        
        Args:
            hostid: ID do host
            
        Returns:
            Dict com informações do host
        """
        params = {
            "output": "extend",
            "hostids": [hostid],
            "selectInterfaces": "extend"
        }
        
        response = self._make_request("host.get", params)
        
        if response and response['result']:
            return response['result'][0]
        
        return None
    
    def get_items_by_name(self, hostid: str, item_name: str) -> Optional[List[Dict]]:
        """
        Busca itens por nome em um host específico
        
        Args:
            hostid: ID do host
            item_name: Nome do item a ser buscado
            
        Returns:
            Lista de itens encontrados
        """
        params = {
            "output": ["itemid", "name", "key_", "status"],
            "hostids": [hostid],
            "search": {
                "name": item_name
            }
        }
        
        response = self._make_request("item.get", params)
        
        if response:
            return response['result']
        
        return None
    
    def create_item(self, hostid: str, interfaceid: str, name: str, key: str, 
                   item_type: int = 0, value_type: int = 3, delay: str = "60s") -> Optional[str]:
        """
        Cria um novo item no Zabbix
        
        Args:
            hostid: ID do host
            interfaceid: ID da interface
            name: Nome do item
            key: Chave do item (comando a ser executado)
            item_type: Tipo do item (0 = Zabbix agent)
            value_type: Tipo de valor (3 = log)
            delay: Intervalo de execução
            
        Returns:
            ID do item criado ou None em caso de erro
        """
        params = {
            "name": name,
            "key_": key,
            "hostid": hostid,
            "type": item_type,
            "value_type": value_type,
            "interfaceid": interfaceid,
            "delay": delay
        }
        
        self.logger.info(f"Criando item '{name}' no host {hostid}")
        response = self._make_request("item.create", params)
        
        if response and 'itemids' in response['result']:
            item_id = response['result']['itemids'][0]
            self.logger.info(f"Item criado com sucesso. ID: {item_id}")
            return item_id
        
        return None
    
    def delete_items(self, item_ids: List[str]) -> bool:
        """
        Exclui itens por ID
        
        Args:
            item_ids: Lista de IDs dos itens a serem excluídos
            
        Returns:
            bool: True se a exclusão foi bem-sucedida
        """
        if not item_ids:
            return True
        
        self.logger.info(f"Excluindo {len(item_ids)} itens...")
        response = self._make_request("item.delete", item_ids)
        
        if response:
            self.logger.info("Itens excluídos com sucesso")
            return True
        
        return False
    
    def cleanup_existing_items(self, hostid: str, item_name: str) -> bool:
        """
        Remove itens existentes com o mesmo nome para evitar duplicação
        
        Args:
            hostid: ID do host
            item_name: Nome do item a ser removido
            
        Returns:
            bool: True se a limpeza foi bem-sucedida
        """
        existing_items = self.get_items_by_name(hostid, item_name)
        
        if existing_items:
            item_ids = [item['itemid'] for item in existing_items]
            self.logger.info(f"Encontrados {len(item_ids)} itens existentes para remoção")
            return self.delete_items(item_ids)
        
        self.logger.info("Nenhum item existente encontrado")
        return True
    
    def get_host_info_summary(self, host: Dict) -> Dict[str, Any]:
        """
        Extrai informações resumidas de um host
        
        Args:
            host: Dict com dados do host
            
        Returns:
            Dict com informações resumidas
        """
        interfaces = host.get('interfaces', [])
        groups = host.get('groups', [])
        
        return {
            'hostid': host.get('hostid'),
            'hostname': host.get('host'),
            'name': host.get('name'),
            'status': 'Ativo' if host.get('status') == '0' else 'Inativo',
            'interfaces_count': len(interfaces),
            'primary_ip': next((iface['ip'] for iface in interfaces if iface.get('main') == '1'), 'N/A'),
            'groups': [group['name'] for group in groups]
        }
    
    def validate_interface(self, host: Dict, interface_index: int = 0) -> Optional[Dict]:
        """
        Valida e retorna uma interface específica de um host
        
        Args:
            host: Dict com dados do host
            interface_index: Índice da interface (padrão: 0)
            
        Returns:
            Dict com dados da interface ou None se inválida
        """
        interfaces = host.get('interfaces', [])
        
        if not interfaces:
            self.logger.error(f"Host {host.get('host')} não possui interfaces")
            return None
        
        if interface_index >= len(interfaces):
            self.logger.error(f"Índice de interface {interface_index} inválido")
            return None
        
        interface = interfaces[interface_index]
        
        # Valida se é uma interface do tipo agent (tipo 1)
        if interface.get('type') != '1':
            self.logger.warning(f"Interface não é do tipo Zabbix Agent")
        
        return interface
