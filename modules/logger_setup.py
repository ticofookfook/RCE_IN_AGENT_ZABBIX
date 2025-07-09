"""
Módulo de configuração de logging
Configura o sistema de logs de forma centralizada
"""

import logging
import sys
from pathlib import Path
from typing import Optional


class LoggerSetup:
    """Configurador de logging centralizado"""
    
    @staticmethod
    def setup_logger(
        name: str = 'zabbix_rce',
        level: str = 'INFO',
        log_file: Optional[str] = None,
        console_output: bool = True
    ) -> logging.Logger:
        """
        Configura e retorna um logger
        
        Args:
            name: Nome do logger
            level: Nível de log (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Arquivo de log (opcional)
            console_output: Se deve exibir logs no console
            
        Returns:
            logging.Logger: Logger configurado
        """
        logger = logging.getLogger(name)
        
        # Remove handlers existentes para evitar duplicação
        logger.handlers.clear()
        
        # Configura nível
        log_level = getattr(logging, level.upper(), logging.INFO)
        logger.setLevel(log_level)
        
        # Formato das mensagens
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Handler para console
        if console_output:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(log_level)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)
        
        # Handler para arquivo
        if log_file:
            try:
                file_handler = logging.FileHandler(log_file, encoding='utf-8')
                file_handler.setLevel(log_level)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.warning(f"Não foi possível criar arquivo de log {log_file}: {e}")
        
        return logger
    
    @staticmethod
    def set_verbose_mode(logger: logging.Logger):
        """Ativa modo verboso (DEBUG) para um logger"""
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
    
    @staticmethod
    def create_colored_formatter():
        """Cria um formatter com cores para o console"""
        try:
            from colorama import init, Fore, Style
            init()
            
            class ColoredFormatter(logging.Formatter):
                COLORS = {
                    'DEBUG': Fore.CYAN,
                    'INFO': Fore.GREEN,
                    'WARNING': Fore.YELLOW,
                    'ERROR': Fore.RED,
                    'CRITICAL': Fore.MAGENTA + Style.BRIGHT,
                }
                
                def format(self, record):
                    color = self.COLORS.get(record.levelname, '')
                    reset = Style.RESET_ALL if color else ''
                    record.levelname = f"{color}{record.levelname}{reset}"
                    return super().format(record)
            
            return ColoredFormatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
        except ImportError:
            # Se colorama não estiver disponível, usa formatter normal
            return logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%H:%M:%S'
            )
