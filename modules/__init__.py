"""
Módulos do Zabbix RCE Exploit
Pacote contendo todos os módulos necessários para o exploit
"""

from .config_manager import ConfigManager
from .logger_setup import LoggerSetup
from .zabbix_api_client import ZabbixAPIClient
from .payload_generator import PayloadGenerator
from .os_detector import OSDetector
from .exploit_manager import ExploitManager
from .user_interface import UserInterface

__all__ = [
    'ConfigManager',
    'LoggerSetup', 
    'ZabbixAPIClient',
    'PayloadGenerator',
    'OSDetector',
    'ExploitManager',
    'UserInterface'
]

__version__ = '2.0.0'
__author__ = 'Zabbix RCE Team'
