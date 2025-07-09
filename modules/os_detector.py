"""
Módulo de detecção de sistema operacional
Identifica o SO baseado em nomes de hosts e outras características
"""

import re
import logging
from typing import Optional, List, Dict


class OSDetector:
    """Detector de sistema operacional baseado em heurísticas"""
    
    def __init__(self):
        self.logger = logging.getLogger('zabbix_rce.os_detector')
        
        # Palavras-chave para detectar Linux
        self.linux_keywords = [
            'linux', 'ubuntu', 'debian', 'centos', 'redhat', 'rhel',
            'fedora', 'suse', 'opensuse', 'arch', 'manjaro', 'mint',
            'kali', 'parrot', 'alpine', 'oracle', 'amazon', 'unix',
            'server', 'srv', 'web', 'db', 'database', 'app'
        ]
        
        # Palavras-chave para detectar Windows
        self.windows_keywords = [
            'win', 'windows', 'ws', 'workstation', 'desktop', 'pc',
            'client', 'laptop', 'notebook', 'server', 'srv', 'dc',
            'domain', 'ad', 'exchange', 'sql', 'iis'
        ]
        
        # Padrões específicos
        self.linux_patterns = [
            r'.*-linux-.*',
            r'.*\.local$',
            r'^(web|db|app|mail|dns|proxy|cache|backup|monitor|log).*',
            r'.*-(prod|dev|test|stage|staging).*'
        ]
        
        self.windows_patterns = [
            r'.*-win-.*',
            r'.*-ws-.*',
            r'.*-pc-.*',
            r'.*\.domain\..*',
            r'^(pc|ws|desktop|laptop|client).*'
        ]
    
    def detect_os_by_hostname(self, hostname: str) -> Optional[str]:
        """
        Detecta SO baseado no nome do host
        
        Args:
            hostname: Nome do host a ser analisado
            
        Returns:
            'Linux', 'Windows' ou None se não conseguir detectar
        """
        if not hostname:
            return None
        
        hostname_lower = hostname.lower().strip()
        self.logger.debug(f"Analisando hostname: {hostname_lower}")
        
        # Verifica padrões específicos primeiro
        for pattern in self.linux_patterns:
            if re.match(pattern, hostname_lower):
                self.logger.debug(f"Padrão Linux encontrado: {pattern}")
                return 'Linux'
        
        for pattern in self.windows_patterns:
            if re.match(pattern, hostname_lower):
                self.logger.debug(f"Padrão Windows encontrado: {pattern}")
                return 'Windows'
        
        # Verifica palavras-chave
        linux_score = 0
        windows_score = 0
        
        for keyword in self.linux_keywords:
            if keyword in hostname_lower:
                linux_score += 1
                self.logger.debug(f"Palavra-chave Linux encontrada: {keyword}")
        
        for keyword in self.windows_keywords:
            if keyword in hostname_lower:
                windows_score += 1
                self.logger.debug(f"Palavra-chave Windows encontrada: {keyword}")
        
        # Determina o SO baseado na pontuação
        if linux_score > windows_score:
            return 'Linux'
        elif windows_score > linux_score:
            return 'Windows'
        
        # Se empate ou nenhuma detecção, tenta heurísticas adicionais
        return self._advanced_detection(hostname_lower)
    
    def _advanced_detection(self, hostname: str) -> Optional[str]:
        """
        Detecção avançada usando heurísticas adicionais
        
        Args:
            hostname: Nome do host em lowercase
            
        Returns:
            'Linux', 'Windows' ou None
        """
        # Heurísticas baseadas em convenções comuns
        
        # Servidores com números geralmente são Linux
        if re.search(r'-\d+$', hostname) or re.search(r'\d+$', hostname):
            if any(srv in hostname for srv in ['srv', 'server', 'node', 'host']):
                return 'Linux'
        
        # Nomes com domínio FQDN geralmente são Windows em ambiente corporativo
        if '.' in hostname and len(hostname.split('.')) > 2:
            return 'Windows'
        
        # Nomes muito curtos e simples geralmente são Linux
        if len(hostname) <= 5 and hostname.isalnum():
            return 'Linux'
        
        # Se contém hífen seguido de números, provavelmente Linux
        if re.search(r'-\d{1,3}$', hostname):
            return 'Linux'
        
        return None
    
    def detect_os_by_interface_info(self, interfaces: List[Dict]) -> Optional[str]:
        """
        Tenta detectar SO baseado nas informações de interface
        
        Args:
            interfaces: Lista de interfaces do host
            
        Returns:
            'Linux', 'Windows' ou None
        """
        if not interfaces:
            return None
        
        # Analisa portas comuns
        ports = []
        for interface in interfaces:
            if 'port' in interface:
                try:
                    port = int(interface['port'])
                    ports.append(port)
                except (ValueError, TypeError):
                    continue
        
        # Porta 10050 é padrão do Zabbix Agent (mais comum em Linux)
        # Porta 10051 é padrão do Zabbix Server
        if 10050 in ports:
            return 'Linux'  # Assume Linux como mais provável
        
        return None
    
    def get_detection_confidence(self, hostname: str) -> Dict[str, float]:
        """
        Retorna o nível de confiança da detecção para cada SO
        
        Args:
            hostname: Nome do host
            
        Returns:
            Dict com scores de confiança para cada SO
        """
        if not hostname:
            return {'Linux': 0.0, 'Windows': 0.0, 'Unknown': 1.0}
        
        hostname_lower = hostname.lower().strip()
        
        linux_score = 0
        windows_score = 0
        total_indicators = 0
        
        # Pontuação por palavras-chave
        for keyword in self.linux_keywords:
            if keyword in hostname_lower:
                linux_score += 1
            total_indicators += 1
        
        for keyword in self.windows_keywords:
            if keyword in hostname_lower:
                windows_score += 1
            total_indicators += 1
        
        # Pontuação por padrões
        for pattern in self.linux_patterns:
            if re.match(pattern, hostname_lower):
                linux_score += 2
            total_indicators += 1
        
        for pattern in self.windows_patterns:
            if re.match(pattern, hostname_lower):
                windows_score += 2
            total_indicators += 1
        
        # Normaliza os scores
        if total_indicators > 0:
            linux_confidence = linux_score / total_indicators
            windows_confidence = windows_score / total_indicators
        else:
            linux_confidence = 0.0
            windows_confidence = 0.0
        
        # Calcula confiança de "Unknown"
        unknown_confidence = 1.0 - max(linux_confidence, windows_confidence)
        
        return {
            'Linux': min(linux_confidence, 1.0),
            'Windows': min(windows_confidence, 1.0),
            'Unknown': max(unknown_confidence, 0.0)
        }
    
    def suggest_os_type(self, hostname: str, interfaces: List[Dict] = None) -> Dict[str, any]:
        """
        Sugere o tipo de SO com informações detalhadas
        
        Args:
            hostname: Nome do host
            interfaces: Lista de interfaces (opcional)
            
        Returns:
            Dict com sugestão e detalhes da detecção
        """
        # Detecção por hostname
        os_by_hostname = self.detect_os_by_hostname(hostname)
        confidence_scores = self.get_detection_confidence(hostname)
        
        # Detecção por interfaces (se disponível)
        os_by_interface = None
        if interfaces:
            os_by_interface = self.detect_os_by_interface_info(interfaces)
        
        # Determina sugestão final
        suggested_os = os_by_hostname
        confidence = "Baixa"
        
        if os_by_hostname:
            max_confidence = max(confidence_scores['Linux'], confidence_scores['Windows'])
            if max_confidence >= 0.7:
                confidence = "Alta"
            elif max_confidence >= 0.4:
                confidence = "Média"
        
        # Se detecção por interface concorda, aumenta confiança
        if os_by_interface and os_by_interface == os_by_hostname:
            if confidence == "Baixa":
                confidence = "Média"
            elif confidence == "Média":
                confidence = "Alta"
        
        return {
            'suggested_os': suggested_os or 'Unknown',
            'confidence': confidence,
            'confidence_scores': confidence_scores,
            'detection_by_hostname': os_by_hostname,
            'detection_by_interface': os_by_interface,
            'hostname_analyzed': hostname
        }
    
    def display_detection_details(self, hostname: str, interfaces: List[Dict] = None):
        """
        Exibe detalhes da detecção de SO
        
        Args:
            hostname: Nome do host
            interfaces: Lista de interfaces (opcional)
        """
        result = self.suggest_os_type(hostname, interfaces)
        
        print(f"\n🔍 Análise de Sistema Operacional para: {hostname}")
        print("=" * 50)
        
        print(f"📊 Sistema Sugerido: {result['suggested_os']}")
        print(f"🎯 Confiança: {result['confidence']}")
        
        print("\n📈 Scores de Confiança:")
        for os_type, score in result['confidence_scores'].items():
            percentage = score * 100
            print(f"   {os_type}: {percentage:.1f}%")
        
        if result['detection_by_interface']:
            print(f"\n🔌 Detecção por Interface: {result['detection_by_interface']}")
        
        print("=" * 50)
