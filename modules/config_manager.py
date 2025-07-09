"""
Módulo de configuração para o Zabbix RCE Exploit
Gerencia todas as configurações e variáveis de ambiente
"""

import os
from dataclasses import dataclass
from dotenv import load_dotenv
from pathlib import Path


@dataclass
class ZabbixConfig:
    """Configurações do Zabbix"""
    url: str
    auth_token: str
    api_timeout: int = 10


@dataclass
class ExploitConfig:
    """Configurações do exploit"""
    ip_shell: str
    port_server_python: int = 9000
    shell_check_delay: int = 60


@dataclass
class LogConfig:
    """Configurações de logging"""
    level: str = "INFO"
    log_file: str = "zabbix_rce.log"


class ConfigManager:
    """Gerenciador de configurações"""
    
    def __init__(self, env_file=".env"):
        # Carrega variáveis de ambiente
        load_dotenv(env_file)
        
        # Inicializa configurações
        self.zabbix = self._load_zabbix_config()
        self.exploit = self._load_exploit_config()
        self.logging = self._load_log_config()
        
        # Valida configurações obrigatórias
        self._validate_config()
    
    def _load_zabbix_config(self) -> ZabbixConfig:
        """Carrega configurações do Zabbix"""
        return ZabbixConfig(
            url=os.getenv('ZABBIX_URL', 'http://127.0.0.1:8080/api_jsonrpc.php'),
            auth_token=os.getenv('AUTH_TOKEN', ''),
            api_timeout=int(os.getenv('API_TIMEOUT', 10))
        )
    
    def _load_exploit_config(self) -> ExploitConfig:
        """Carrega configurações do exploit"""
        return ExploitConfig(
            ip_shell=os.getenv('IP_SHELL', '127.0.0.1'),
            port_server_python=int(os.getenv('PORT_SERVER_PYTHON', 9000)),
            shell_check_delay=int(os.getenv('SHELL_CHECK_DELAY', 60))
        )
    
    def _load_log_config(self) -> LogConfig:
        """Carrega configurações de logging"""
        return LogConfig(
            level=os.getenv('LOG_LEVEL', 'INFO'),
            log_file=os.getenv('LOG_FILE', 'zabbix_rce.log')
        )
    
    def _validate_config(self):
        """Valida configurações obrigatórias"""
        if not self.zabbix.auth_token:
            raise ValueError("AUTH_TOKEN é obrigatório no arquivo .env")
        
        if not self.zabbix.url:
            raise ValueError("ZABBIX_URL é obrigatório no arquivo .env")
        
        if not self.exploit.ip_shell:
            raise ValueError("IP_SHELL é obrigatório no arquivo .env")
    
    def get_headers(self) -> dict:
        """Retorna headers padrão para requisições"""
        return {'Content-Type': 'application/json'}
    
    def display_config(self):
        """Exibe configurações atuais (sem dados sensíveis)"""
        print("=== Configurações Atuais ===")
        print(f"Zabbix URL: {self.zabbix.url}")
        print(f"IP Shell: {self.exploit.ip_shell}")
        print(f"Porta Servidor: {self.exploit.port_server_python}")
        print(f"Timeout API: {self.zabbix.api_timeout}s")
        print(f"Log Level: {self.logging.level}")
        print("=" * 30)
