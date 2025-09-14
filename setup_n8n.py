#!/usr/bin/env python3

import os
import subprocess
import urllib.request
import tarfile
import shutil
import pathlib
import json
import sys
import logging
import hashlib
import time
import threading
from typing import Tuple, Optional, Dict, List, Callable
from datetime import datetime
from dataclasses import dataclass
from pathlib import Path

# Configurações de cores e estilos
class Colors:
    RESET = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    BLINK = '\033[5m'
    REVERSE = '\033[7m'
    
    # Cores básicas
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    WHITE = '\033[37m'
    
    # Cores brilhantes
    BRIGHT_BLACK = '\033[90m'
    BRIGHT_RED = '\033[91m'
    BRIGHT_GREEN = '\033[92m'
    BRIGHT_YELLOW = '\033[93m'
    BRIGHT_BLUE = '\033[94m'
    BRIGHT_MAGENTA = '\033[95m'
    BRIGHT_CYAN = '\033[96m'
    BRIGHT_WHITE = '\033[97m'
    
    # Backgrounds
    BG_BLACK = '\033[40m'
    BG_RED = '\033[41m'
    BG_GREEN = '\033[42m'
    BG_YELLOW = '\033[43m'
    BG_BLUE = '\033[44m'
    BG_MAGENTA = '\033[45m'
    BG_CYAN = '\033[46m'
    BG_WHITE = '\033[47m'

class Icons:
    # Símbolos modernos
    ROCKET = '🚀'
    GEAR = '⚙️'
    PACKAGE = '📦'
    DOWNLOAD = '⬇️'
    UPLOAD = '⬆️'
    CHECK = '✅'
    CROSS = '❌'
    WARNING = '⚠️'
    INFO = 'ℹ️'
    STAR = '⭐'
    FIRE = '🔥'
    LIGHTNING = '⚡'
    DIAMOND = '💎'
    CROWN = '👑'
    MAGIC = '✨'
    CLOCK = '⏰'
    FOLDER = '📁'
    FILE = '📄'
    COMPUTER = '💻'
    NETWORK = '🌐'
    SHIELD = '🛡️'
    TARGET = '🎯'
    CHART = '📊'
    TOOLS = '🛠️'
    CLEAN = '🧹'
    EXIT = '🚪'
    ARROW_RIGHT = '▶️'
    ARROW_LEFT = '◀️'
    ARROW_UP = '⬆️'
    ARROW_DOWN = '⬇️'
    DOUBLE_ARROW = '⩺'
    REFRESH = '🔄'
    SUCCESS = '🎉'
    BUILD = '🏗️'
    DEPLOY = '🚀'
    CONFIG = '⚡'
    GIT = '🔧'

@dataclass
class MenuItem:
    id: str
    title: str
    description: str
    icon: str
    action: Optional[Callable] = None
    category: str = "main"
    requires_confirmation: bool = False
    danger_level: str = "safe"  # safe, warning, danger
    estimated_time: str = "< 1min"

class AnimatedSpinner:
    def __init__(self, message="Processando"):
        self.message = message
        self.running = False
        self.thread = None
        self.frames = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        
    def _spin(self):
        frame_index = 0
        while self.running:
            frame = self.frames[frame_index % len(self.frames)]
            print(f'\r{Colors.BRIGHT_CYAN}{frame} {self.message}{Colors.RESET}', end='', flush=True)
            time.sleep(0.1)
            frame_index += 1
        print('\r' + ' ' * (len(self.message) + 10) + '\r', end='', flush=True)
    
    def start(self):
        self.running = True
        self.thread = threading.Thread(target=self._spin)
        self.thread.daemon = True
        self.thread.start()
    
    def stop(self):
        self.running = False
        if self.thread:
            self.thread.join()

class ModernUI:
    def __init__(self):
        self.width = self._get_terminal_width()
        self.spinner = None
        
    def _get_terminal_width(self):
        try:
            return os.get_terminal_size().columns
        except:
            return 80
    
    def clear_screen(self):
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def print_gradient_line(self, char='═', color_start=Colors.BRIGHT_MAGENTA, color_end=Colors.BRIGHT_CYAN):
        gradient = f"{color_start}{char * (self.width//2)}{color_end}{char * (self.width//2)}{Colors.RESET}"
        print(gradient)
    
    def print_header(self, title: str, subtitle: str = ""):
        self.clear_screen()
        
        # Header com gradiente
        self.print_gradient_line('═', Colors.BRIGHT_MAGENTA, Colors.BRIGHT_CYAN)
        
        # Título principal com efeito
        title_line = f"{Colors.BOLD}{Colors.BRIGHT_WHITE}{Icons.DIAMOND} {title.upper()} {Icons.DIAMOND}{Colors.RESET}"
        padding = (self.width - len(title.strip()) - 4) // 2
        print(f"{' ' * padding}{title_line}")
        
        if subtitle:
            subtitle_line = f"{Colors.DIM}{Colors.BRIGHT_CYAN}{subtitle}{Colors.RESET}"
            sub_padding = (self.width - len(subtitle)) // 2
            print(f"{' ' * sub_padding}{subtitle_line}")
        
        self.print_gradient_line('═', Colors.BRIGHT_CYAN, Colors.BRIGHT_MAGENTA)
        print()
    
    def print_category_header(self, category: str, description: str = ""):
        print(f"\n{Colors.BOLD}{Colors.BG_BLUE}{Colors.WHITE} {category.upper()} {Colors.RESET}")
        if description:
            print(f"{Colors.DIM}{Colors.BRIGHT_CYAN}{description}{Colors.RESET}")
        print(f"{Colors.BRIGHT_BLUE}{'─' * 50}{Colors.RESET}")
    
    def print_menu_item(self, index: int, item: MenuItem, is_selected: bool = False):
        # Cores baseadas no nível de perigo
        danger_colors = {
            "safe": Colors.BRIGHT_GREEN,
            "warning": Colors.BRIGHT_YELLOW,
            "danger": Colors.BRIGHT_RED
        }
        
        color = danger_colors.get(item.danger_level, Colors.BRIGHT_GREEN)
        
        if is_selected:
            bg_color = Colors.BG_CYAN
            text_color = Colors.BLACK
            marker = f"{Colors.BRIGHT_YELLOW}▶{Colors.RESET}"
        else:
            bg_color = ""
            text_color = Colors.BRIGHT_WHITE
            marker = " "
        
        # Formatação da linha
        index_str = f"{Colors.DIM}[{index:02d}]{Colors.RESET}"
        icon_str = f"{color}{item.icon}{Colors.RESET}"
        title_str = f"{bg_color}{text_color}{Colors.BOLD}{item.title}{Colors.RESET}"
        desc_str = f"{Colors.DIM}{item.description}{Colors.RESET}"
        time_str = f"{Colors.BRIGHT_BLACK}({item.estimated_time}){Colors.RESET}"
        
        print(f"{marker} {index_str} {icon_str} {title_str}")
        print(f"    {desc_str} {time_str}")
        
        if item.requires_confirmation:
            print(f"    {Colors.BRIGHT_YELLOW}{Icons.WARNING} Requer confirmação{Colors.RESET}")
    
    def print_status_bar(self, status: str, progress: Optional[int] = None):
        status_line = f"{Colors.BG_BLACK}{Colors.BRIGHT_WHITE} STATUS: {status} {Colors.RESET}"
        
        if progress is not None:
            progress_bar = self._create_progress_bar(progress)
            status_line += f" {progress_bar}"
        
        print(f"\n{status_line}")
    
    def _create_progress_bar(self, percentage: int, width: int = 30):
        filled = int(width * percentage / 100)
        bar = f"{Colors.BRIGHT_GREEN}{'█' * filled}{Colors.BRIGHT_BLACK}{'░' * (width - filled)}{Colors.RESET}"
        return f"[{bar}] {percentage}%"
    
    def print_info_box(self, title: str, content: List[str], icon: str = Icons.INFO):
        print(f"\n{Colors.BRIGHT_CYAN}╭─ {icon} {title} {'─' * (50 - len(title))}╮{Colors.RESET}")
        for line in content:
            print(f"{Colors.BRIGHT_CYAN}│{Colors.RESET} {line:<48} {Colors.BRIGHT_CYAN}│{Colors.RESET}")
        print(f"{Colors.BRIGHT_CYAN}╰{'─' * 50}╯{Colors.RESET}")
    
    def print_success(self, message: str):
        print(f"\n{Colors.BRIGHT_GREEN}{Icons.SUCCESS} {message}{Colors.RESET}")
    
    def print_error(self, message: str):
        print(f"\n{Colors.BRIGHT_RED}{Icons.CROSS} {message}{Colors.RESET}")
    
    def print_warning(self, message: str):
        print(f"\n{Colors.BRIGHT_YELLOW}{Icons.WARNING} {message}{Colors.RESET}")
    
    def get_input(self, prompt: str, options: List[str] = None) -> str:
        if options:
            options_str = f"[{'/'.join(options)}]"
            full_prompt = f"{Colors.BRIGHT_CYAN}{Icons.ARROW_RIGHT} {prompt} {Colors.DIM}{options_str}{Colors.RESET}: "
        else:
            full_prompt = f"{Colors.BRIGHT_CYAN}{Icons.ARROW_RIGHT} {prompt}{Colors.RESET}: "
        
        return input(full_prompt).strip()
    
    def confirm(self, message: str, danger: bool = False) -> bool:
        color = Colors.BRIGHT_RED if danger else Colors.BRIGHT_YELLOW
        icon = Icons.WARNING if danger else Icons.INFO
        
        response = self.get_input(f"{color}{icon} {message}", ["y", "N"])
        return response.lower() in ['y', 'yes', 'sim', 's']
    
    def show_loading(self, message: str):
        self.spinner = AnimatedSpinner(message)
        self.spinner.start()
    
    def hide_loading(self):
        if self.spinner:
            self.spinner.stop()
            self.spinner = None

# Configuração de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('build_script.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Configurações globais
home = pathlib.Path.home()
current_dir = Path.cwd()
repo_dir = current_dir / "n8n"
local_dir = repo_dir / ".local"
bin_dir = local_dir / "bin"
node_dir = None

# Interface do usuário
ui = ModernUI()

class BuildSystem:
    def __init__(self):
        self.status = "Inicializado"
        self.stats = {
            'git_cloned': False,
            'node_version': None,
            'pnpm_version': None,
            'build_time': None,
            'package_size': None,
            'last_build': None
        }
    
    def run_command(self, cmd: str, cwd: Optional[pathlib.Path] = None, capture_output: bool = False, shell: bool = True) -> Optional[str]:
        """Executa um comando shell com tratamento de erro melhorado"""
        try:
            logger.info(f"Executando comando: {cmd}")
            if cwd:
                logger.info(f"Diretório: {cwd}")
            
            # Garante que o PATH inclui os binários locais
            env = os.environ.copy()
            if node_dir and (node_dir / "bin").exists():
                node_bin_path = str(node_dir / "bin")
                if node_bin_path not in env.get("PATH", ""):
                    env["PATH"] = f"{node_bin_path}:{env.get('PATH', '')}"
            
            if bin_dir.exists():
                bin_path = str(bin_dir)
                if bin_path not in env.get("PATH", ""):
                    env["PATH"] = f"{bin_path}:{env.get('PATH', '')}"
            
            result = subprocess.run(
                cmd, 
                shell=shell, 
                check=True, 
                cwd=cwd,
                capture_output=capture_output,
                text=True,
                env=env
            )
            
            if capture_output:
                return result.stdout.strip()
            return None
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Erro ao executar comando '{cmd}': {e}")
            logger.error(f"Código de saída: {e.returncode}")
            if hasattr(e, 'stderr') and e.stderr:
                logger.error(f"Erro stderr: {e.stderr}")
            if hasattr(e, 'stdout') and e.stdout:
                logger.error(f"Stdout: {e.stdout}")
            raise

    def download_with_progress(self, url: str, destination: pathlib.Path) -> None:
        """Download de arquivo com indicador de progresso"""
        logger.info(f"Baixando {url} para {destination}")
        
        def progress_hook(block_num, block_size, total_size):
            if total_size > 0:
                percent = min(100, (block_num * block_size * 100) // total_size)
                print(f"\r{Colors.BRIGHT_CYAN}⬇️ Progresso: {percent}%{Colors.RESET}", end='', flush=True)
        
        try:
            urllib.request.urlretrieve(url, destination, progress_hook)
            print()  # Nova linha após o progresso
            logger.info(f"Download concluído: {destination}")
        except Exception as e:
            logger.error(f"Erro no download: {e}")
            if destination.exists():
                destination.unlink()
            raise

    def verify_file_integrity(self, file_path: pathlib.Path, expected_hash: Optional[str] = None) -> bool:
        """Verifica a integridade do arquivo baixado"""
        if not file_path.exists():
            return False
        
        if expected_hash:
            with open(file_path, 'rb') as f:
                file_hash = hashlib.sha256(f.read()).hexdigest()
            return file_hash == expected_hash
        
        return file_path.stat().st_size > 0

    def clone_n8n_repository(self):
        """Clona o repositório N8N"""
        ui.print_info_box("Clonando Repositório", [
            "Fazendo git clone do repositório N8N...",
            "URL: https://github.com/ilyra-ai/n8n.git",
            "Configurando permissões..."
        ], Icons.GIT)
        
        if repo_dir.exists():
            ui.print_warning("Diretório n8n já existe!")
            if ui.confirm("Deseja remover o diretório existente e clonar novamente?", danger=True):
                ui.show_loading("Removendo diretório existente")
                shutil.rmtree(repo_dir, ignore_errors=True)
                ui.hide_loading()
            else:
                ui.print_info_box("Pulando Clone", [
                    "Usando repositório existente",
                    "Apenas configurando permissões..."
                ], Icons.INFO)
                self._set_permissions()
                self.stats['git_cloned'] = True
                return
        
        ui.show_loading("Clonando repositório N8N")
        
        try:
            # Git clone
            self.run_command(
                "git clone https://github.com/ilyra-ai/n8n.git",
                cwd=current_dir
            )
            ui.hide_loading()
            ui.print_success("Repositório clonado com sucesso")
            
            # Configurar permissões
            self._set_permissions()
            
            self.stats['git_cloned'] = True
            
        except Exception as e:
            ui.hide_loading()
            ui.print_error(f"Erro no clone: {str(e)}")
            raise

    def _set_permissions(self):
        """Configura permissões do diretório"""
        ui.show_loading("Configurando permissões")
        try:
            self.run_command(f"sudo chmod 777 -R {repo_dir}")
            ui.hide_loading()
            ui.print_success("Permissões configuradas")
        except Exception as e:
            ui.hide_loading()
            ui.print_warning(f"Erro ao configurar permissões: {str(e)}")

    def get_latest_node_lts(self) -> Tuple[str, str]:
        """Obtém a versão LTS mais recente do Node.js"""
        ui.show_loading("Buscando versão LTS mais recente do Node.js")
        
        try:
            with urllib.request.urlopen("https://nodejs.org/dist/index.json") as response:
                data = json.loads(response.read().decode())
            
            for entry in data:
                if entry.get("lts"):
                    version = entry["version"]
                    filename = f"node-{version}-linux-x64.tar.xz"
                    url = f"https://nodejs.org/dist/{version}/{filename}"
                    ui.hide_loading()
                    ui.print_success(f"Versão LTS encontrada: {version}")
                    return version, url
                    
        except Exception as e:
            ui.hide_loading()
            ui.print_warning(f"Erro ao buscar versão do Node.js: {e}")
            ui.print_info_box("Usando Fallback", [
                "Será utilizada uma versão LTS conhecida e estável",
                "Versão: v20.18.0"
            ], Icons.INFO)
            version = "v20.18.0"
            filename = f"node-{version}-linux-x64.tar.xz"
            url = f"https://nodejs.org/dist/{version}/{filename}"
            return version, url
        
        raise RuntimeError("Não foi possível determinar a versão LTS do Node.js")

    def ensure_node(self):
        """Garante que o Node.js esteja instalado localmente"""
        global node_dir
        
        ui.print_info_box("Verificando Node.js", [
            "Verificando instalação local do Node.js...",
            "Será baixado automaticamente se necessário"
        ], Icons.COMPUTER)
        
        version, url = self.get_latest_node_lts()
        node_dir = local_dir / f"node-{version}-linux-x64"
        node_binary = node_dir / "bin" / "node"
        
        if node_binary.exists():
            try:
                installed_version = self.run_command(f"{node_binary} --version", capture_output=True)
                self.stats['node_version'] = installed_version
                ui.print_success(f"Node.js já instalado: {installed_version}")
                return
            except:
                ui.print_warning("Node.js instalado mas não funcional, reinstalando...")
                shutil.rmtree(node_dir, ignore_errors=True)
        
        ui.show_loading("Instalando Node.js")
        local_dir.mkdir(parents=True, exist_ok=True)
        
        archive_name = f"node-{version}-linux-x64.tar.xz"
        archive_path = local_dir / archive_name
        
        # Download do arquivo se necessário
        if not archive_path.exists() or not self.verify_file_integrity(archive_path):
            ui.hide_loading()
            self.download_with_progress(url, archive_path)
            ui.show_loading("Extraindo arquivos")
        
        # Extração
        try:
            with tarfile.open(archive_path, "r:xz") as tar_file:
                tar_file.extractall(path=local_dir)
            ui.hide_loading()
            ui.print_success("Node.js instalado com sucesso")
        except Exception as e:
            ui.hide_loading()
            ui.print_error(f"Erro na extração: {e}")
            if archive_path.exists():
                archive_path.unlink()
            raise
        
        # Verifica se a instalação foi bem-sucedida
        if not node_binary.exists():
            raise RuntimeError("Falha na instalação do Node.js")
        
        # Atualiza PATH
        node_bin_path = str(node_dir / "bin")
        current_path = os.environ.get("PATH", "")
        if node_bin_path not in current_path:
            os.environ["PATH"] = f"{node_bin_path}:{current_path}"
        
        # Atualiza stats
        self.stats['node_version'] = self.run_command(f"{node_binary} --version", capture_output=True)

    def ensure_pnpm(self):
        """Garante que o pnpm esteja instalado"""
        ui.print_info_box("Verificando pnpm", [
            "Verificando gerenciador de pacotes pnpm...",
            "Será instalado automaticamente se necessário"
        ], Icons.PACKAGE)
        
        # Primeiro tenta usar pnpm global se disponível
        try:
            version = self.run_command("pnpm --version", cwd=repo_dir, capture_output=True)
            self.stats['pnpm_version'] = version
            ui.print_success(f"pnpm já disponível: v{version}")
            return
        except:
            pass
        
        # Tenta usar pnpm local se existe
        pnpm_binary = bin_dir / "pnpm"
        if pnpm_binary.exists():
            try:
                version = self.run_command(f"{pnpm_binary} --version", cwd=repo_dir, capture_output=True)
                self.stats['pnpm_version'] = version
                ui.print_success(f"pnpm local já instalado: v{version}")
                return
            except:
                ui.print_warning("pnpm instalado mas não funcional, reinstalando...")
                pnpm_binary.unlink(missing_ok=True)
        
        ui.show_loading("Instalando pnpm")
        bin_dir.mkdir(parents=True, exist_ok=True)
        
        npm_binary = node_dir / "bin" / "npm"
        if not npm_binary.exists():
            ui.hide_loading()
            raise RuntimeError("npm não encontrado. Instale o Node.js primeiro.")
        
        try:
            # Instala pnpm usando npm
            self.run_command(f"{npm_binary} install -g pnpm@latest --prefix {local_dir}", cwd=repo_dir)
            ui.hide_loading()
            
            # Verifica se foi instalado corretamente
            if pnpm_binary.exists():
                ui.print_success("pnpm instalado com sucesso")
                # Atualiza PATH
                bin_path = str(bin_dir)
                current_path = os.environ.get("PATH", "")
                if bin_path not in current_path:
                    os.environ["PATH"] = f"{bin_path}:{current_path}"
                # Atualiza stats
                self.stats['pnpm_version'] = self.run_command(f"{pnpm_binary} --version", cwd=repo_dir, capture_output=True)
            else:
                raise RuntimeError("Falha na instalação do pnpm")
                
        except Exception as e:
            ui.hide_loading()
            ui.print_error(f"Erro na instalação do pnpm: {str(e)}")
            raise

    def check_project_structure(self):
        """Verifica se a estrutura do projeto está correta"""
        ui.show_loading("Verificando estrutura do projeto")
        
        if not repo_dir.exists():
            ui.hide_loading()
            raise RuntimeError(f"Diretório do projeto não encontrado: {repo_dir}")
        
        package_json = repo_dir / "package.json"
        if not package_json.exists():
            ui.hide_loading()
            raise RuntimeError(f"package.json não encontrado em {repo_dir}")
        
        ui.hide_loading()
        ui.print_success("Estrutura do projeto validada")

    def build_project(self):
        """Executa o build do projeto"""
        start_time = time.time()
        
        ui.print_info_box("Iniciando Build", [
            "Verificando dependências...",
            "Executando processo de build...",
            "Este processo pode demorar alguns minutos"
        ], Icons.BUILD)
        
        self.check_project_structure()
        
        # Instala dependências se necessário
        node_modules = repo_dir / "node_modules"
        if not node_modules.exists():
            ui.show_loading("Instalando dependências do projeto")
            
            # Tenta diferentes formas de executar pnpm install
            try:
                # Primeiro tenta com pnpm local
                if (bin_dir / "pnpm").exists():
                    self.run_command(f"{bin_dir / 'pnpm'} install", cwd=repo_dir)
                else:
                    # Tenta com pnpm global
                    self.run_command("pnpm install", cwd=repo_dir)
                    
                ui.hide_loading()
                ui.print_success("Dependências instaladas")
                
            except Exception as e:
                ui.hide_loading()
                ui.print_error(f"Erro na instalação das dependências: {str(e)}")
                ui.print_info_box("Tentando alternativa com npm", [
                    "Usando npm como fallback...",
                    "Este processo pode ser mais lento"
                ], Icons.WARNING)
                
                # Fallback para npm
                npm_binary = node_dir / "bin" / "npm"
                if npm_binary.exists():
                    ui.show_loading("Instalando dependências com npm")
                    self.run_command(f"{npm_binary} install", cwd=repo_dir)
                    ui.hide_loading()
                    ui.print_success("Dependências instaladas com npm")
                else:
                    raise RuntimeError("Nem pnpm nem npm estão funcionais")
        
        # Executa o build
        ui.show_loading("Executando build do projeto")
        try:
            # Tenta diferentes comandos de build
            if (bin_dir / "pnpm").exists():
                self.run_command(f"{bin_dir / 'pnpm'} run build:deploy", cwd=repo_dir)
            else:
                self.run_command("pnpm run build:deploy", cwd=repo_dir)
        except:
            # Fallback para npm
            npm_binary = node_dir / "bin" / "npm"
            if npm_binary.exists():
                self.run_command(f"{npm_binary} run build:deploy", cwd=repo_dir)
            else:
                raise
        
        ui.hide_loading()
        
        build_time = time.time() - start_time
        self.stats['build_time'] = f"{build_time:.2f}s"
        self.stats['last_build'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        ui.print_success(f"Build concluído em {build_time:.2f} segundos")

    def create_package(self):
        """Cria o pacote final"""
        ui.print_info_box("Criando Pacote", [
            "Preparando diretório de distribuição...",
            "Copiando Node.js runtime...",
            "Compactando arquivos..."
        ], Icons.PACKAGE)
        
        ui.show_loading("Preparando diretório de distribuição")
        
        compiled_dir = repo_dir / "compiled"
        
        # Remove diretório compilado anterior se existir
        if compiled_dir.exists():
            shutil.rmtree(compiled_dir)
        
        compiled_dir.mkdir(parents=True, exist_ok=True)
        
        # Copia Node.js para o pacote
        node_target = compiled_dir / "node"
        if node_dir and node_dir.exists():
            ui.hide_loading()
            ui.show_loading("Copiando Node.js runtime")
            shutil.copytree(node_dir, node_target, dirs_exist_ok=True)
            ui.hide_loading()
        else:
            ui.hide_loading()
            raise RuntimeError("Diretório do Node.js não encontrado")
        
        # Copia os arquivos build do projeto
        dist_dir = repo_dir / "dist"
        if dist_dir.exists():
            ui.show_loading("Copiando arquivos de build")
            shutil.copytree(dist_dir, compiled_dir / "dist", dirs_exist_ok=True)
            ui.hide_loading()
        
        # Copia outros arquivos necessários
        essential_files = ["package.json", "package-lock.json"]
        for file_name in essential_files:
            file_path = repo_dir / file_name
            if file_path.exists():
                shutil.copy2(file_path, compiled_dir)
        
        # Cria arquivo ZIP
        archive_name = repo_dir / "n8n_complete"
        zip_file = archive_name.with_suffix('.zip')
        
        if zip_file.exists():
            zip_file.unlink()
        
        ui.show_loading("Compactando arquivos")
        shutil.make_archive(str(archive_name), "zip", root_dir=compiled_dir)
        ui.hide_loading()
        
        if zip_file.exists():
            file_size = zip_file.stat().st_size / (1024 * 1024)  # MB
            self.stats['package_size'] = f"{file_size:.2f} MB"
            ui.print_success(f"Pacote criado: {zip_file} ({file_size:.2f} MB)")
        else:
            raise RuntimeError("Falha na criação do pacote")

    def cleanup_temp_files(self):
        """Remove arquivos temporários"""
        ui.show_loading("Removendo arquivos temporários")
        
        removed_count = 0
        temp_patterns = ["node-*.tar.xz", "*.tmp", "*.log.old"]
        
        for pattern in temp_patterns:
            for file_path in local_dir.glob(pattern):
                if file_path.is_file():
                    file_path.unlink()
                    removed_count += 1
        
        ui.hide_loading()
        ui.print_success(f"Removidos {removed_count} arquivos temporários")

    def show_system_info(self):
        """Mostra informações do sistema"""
        system_info = [
            f"Diretório atual: {current_dir}",
            f"Diretório do projeto: {repo_dir}",
            f"Diretório local: {local_dir}",
            f"Git clonado: {'Sim' if self.stats.get('git_cloned') else 'Não'}",
            f"Node.js versão: {self.stats.get('node_version', 'Não instalado')}",
            f"pnpm versão: {self.stats.get('pnpm_version', 'Não instalado')}",
            f"Último build: {self.stats.get('last_build', 'Nunca')}",
            f"Tempo do último build: {self.stats.get('build_time', 'N/A')}",
            f"Tamanho do pacote: {self.stats.get('package_size', 'N/A')}"
        ]
        
        ui.print_info_box("Informações do Sistema", system_info, Icons.COMPUTER)

class MenuManager:
    def __init__(self, build_system: BuildSystem):
        self.build_system = build_system
        self.categories = self._create_menu_structure()
        self.current_category = "main"
    
    def _create_menu_structure(self) -> Dict[str, List[MenuItem]]:
        return {
            "main": [
                MenuItem(
                    "setup_complete", 
                    "Setup Completo Automático", 
                    "Clone + Node.js + pnpm + build + package (tudo automatizado)",
                    Icons.ROCKET,
                    self._complete_setup,
                    estimated_time="5-8min"
                ),
                MenuItem(
                    "step_by_step", 
                    "Setup Passo a Passo", 
                    "Execute cada etapa individualmente com controle total",
                    Icons.TARGET,
                    lambda: self._change_category("setup"),
                    estimated_time="8-15min"
                ),
                MenuItem(
                    "build_only", 
                    "Build e Package Apenas", 
                    "Se o repositório já existe, fazer apenas build + package",
                    Icons.BUILD,
                    lambda: self._change_category("build"),
                    estimated_time="3-5min"
                ),
                MenuItem(
                    "maintenance", 
                    "Manutenção & Limpeza", 
                    "Ferramentas de manutenção, limpeza e diagnóstico",
                    Icons.TOOLS,
                    lambda: self._change_category("maintenance"),
                    estimated_time="< 1min"
                ),
                MenuItem(
                    "info", 
                    "Informações do Sistema", 
                    "Visualizar status, versões e estatísticas",
                    Icons.INFO,
                    self.build_system.show_system_info,
                    estimated_time="< 1min"
                ),
                MenuItem(
                    "exit", 
                    "Sair", 
                    "Encerrar o programa",
                    Icons.EXIT,
                    self._exit_program,
                    danger_level="safe"
                ),
            ],
            
            "setup": [
                MenuItem(
                    "clone_repo", 
                    "Clonar Repositório N8N", 
                    "Git clone + configuração de permissões",
                    Icons.GIT,
                    self.build_system.clone_n8n_repository,
                    estimated_time="1-2min"
                ),
                MenuItem(
                    "install_node", 
                    "Instalar/Verificar Node.js", 
                    "Download e instalação automática do Node.js LTS",
                    Icons.DOWNLOAD,
                    self.build_system.ensure_node,
                    estimated_time="1-2min"
                ),
                MenuItem(
                    "install_pnpm", 
                    "Instalar/Verificar pnpm", 
                    "Instalação do gerenciador de pacotes pnpm",
                    Icons.PACKAGE,
                    self.build_system.ensure_pnpm,
                    estimated_time="30s"
                ),
                MenuItem(
                    "build_project", 
                    "Executar Build", 
                    "Compilar o projeto com todas as dependências",
                    Icons.BUILD,
                    self.build_system.build_project,
                    estimated_time="2-3min"
                ),
                MenuItem(
                    "create_package", 
                    "Criar Pacote Final", 
                    "Gerar arquivo ZIP com runtime completo",
                    Icons.PACKAGE,
                    self.build_system.create_package,
                    estimated_time="30s"
                ),
                MenuItem(
                    "back", 
                    "Voltar ao Menu Principal", 
                    "Retornar para o menu principal",
                    Icons.ARROW_LEFT,
                    lambda: self._change_category("main")
                ),
            ],
            
            "build": [
                MenuItem(
                    "check_repo", 
                    "Verificar Repositório", 
                    "Verifica se o repositório N8N existe e está válido",
                    Icons.SHIELD,
                    self._check_existing_repo,
                    estimated_time="10s"
                ),
                MenuItem(
                    "build_project", 
                    "Executar Build", 
                    "Compilar o projeto com todas as dependências",
                    Icons.BUILD,
                    self.build_system.build_project,
                    estimated_time="2-3min"
                ),
                MenuItem(
                    "create_package", 
                    "Criar Pacote Final", 
                    "Gerar arquivo ZIP com runtime completo",
                    Icons.PACKAGE,
                    self.build_system.create_package,
                    estimated_time="30s"
                ),
                MenuItem(
                    "quick_build", 
                    "Build + Package Rápido", 
                    "Executa build e package automaticamente",
                    Icons.LIGHTNING,
                    self._quick_build_only,
                    estimated_time="2-4min"
                ),
                MenuItem(
                    "back", 
                    "Voltar ao Menu Principal", 
                    "Retornar para o menu principal",
                    Icons.ARROW_LEFT,
                    lambda: self._change_category("main")
                ),
            ],
            
            "maintenance": [
                MenuItem(
                    "cleanup", 
                    "Limpar Arquivos Temporários", 
                    "Remove downloads e arquivos temporários",
                    Icons.CLEAN,
                    self.build_system.cleanup_temp_files,
                    estimated_time="< 30s"
                ),
                MenuItem(
                    "force_reinstall_node", 
                    "Reinstalar Node.js", 
                    "Força reinstalação completa do Node.js",
                    Icons.REFRESH,
                    self._force_reinstall_node,
                    requires_confirmation=True,
                    danger_level="warning",
                    estimated_time="1-2min"
                ),
                MenuItem(
                    "force_reinstall_pnpm", 
                    "Reinstalar pnpm", 
                    "Força reinstalação completa do pnpm",
                    Icons.REFRESH,
                    self._force_reinstall_pnpm,
                    requires_confirmation=True,
                    danger_level="warning",
                    estimated_time="30s"
                ),
                MenuItem(
                    "reset_repo", 
                    "Reset Repositório", 
                    "Remove e re-clona o repositório N8N",
                    Icons.WARNING,
                    self._reset_repository,
                    requires_confirmation=True,
                    danger_level="danger",
                    estimated_time="2-3min"
                ),
                MenuItem(
                    "reset_all", 
                    "Reset Completo", 
                    "Remove tudo e reinicia do zero (CUIDADO!)",
                    Icons.WARNING,
                    self._reset_all,
                    requires_confirmation=True,
                    danger_level="danger",
                    estimated_time="1min"
                ),
                MenuItem(
                    "check_health", 
                    "Diagnóstico do Sistema", 
                    "Verifica integridade de todas as instalações",
                    Icons.SHIELD,
                    self._system_health_check,
                    estimated_time="30s"
                ),
                MenuItem(
                    "back", 
                    "Voltar ao Menu Principal", 
                    "Retornar para o menu principal",
                    Icons.ARROW_LEFT,
                    lambda: self._change_category("main")
                ),
            ]
        }
    
    def _change_category(self, category: str):
        """Muda a categoria atual do menu"""
        self.current_category = category
    
    def _exit_program(self):
        """Encerra o programa com estilo"""
        ui.clear_screen()
        ui.print_header("ENCERRANDO", "Obrigado por usar o Build System!")
        
        farewell_messages = [
            f"{Icons.SUCCESS} Build system finalizado com sucesso!",
            f"{Icons.CLOCK} Sessão encerrada em: {datetime.now().strftime('%H:%M:%S')}",
            f"{Icons.MAGIC} Até a próxima! {Icons.ROCKET}"
        ]
        
        for msg in farewell_messages:
            print(f"  {msg}")
            time.sleep(0.5)
        
        print(f"\n{Colors.BRIGHT_CYAN}{'═' * ui.width}{Colors.RESET}")
        sys.exit(0)
    
    def _complete_setup(self):
        """Executa setup completo automaticamente"""
        ui.print_header("SETUP AUTOMÁTICO COMPLETO", "Executando todas as etapas automaticamente")
        
        if not ui.confirm("Deseja executar o setup completo automático (clone + build + package)?"):
            ui.print_warning("Operação cancelada pelo usuário")
            return
        
        steps = [
            ("Clonando repositório N8N", self.build_system.clone_n8n_repository),
            ("Instalando Node.js", self.build_system.ensure_node),
            ("Instalando pnpm", self.build_system.ensure_pnpm),
            ("Executando build", self.build_system.build_project),
            ("Criando pacote", self.build_system.create_package)
        ]
        
        start_time = time.time()
        
        try:
            for i, (step_name, step_func) in enumerate(steps, 1):
                ui.print_info_box(f"Etapa {i}/{len(steps)}", [step_name], Icons.GEAR)
                step_func()
                time.sleep(0.5)  # Pequena pausa para melhor UX
            
            total_time = time.time() - start_time
            
            ui.print_header("SETUP CONCLUÍDO!", f"Tempo total: {total_time:.2f} segundos")
            ui.print_success("Todas as etapas foram executadas com sucesso!")
            
            # Mostra resumo final
            summary = [
                f"Repositório: {'Clonado' if self.build_system.stats.get('git_cloned') else 'Erro'}",
                f"Node.js: {self.build_system.stats.get('node_version', 'N/A')}",
                f"pnpm: v{self.build_system.stats.get('pnpm_version', 'N/A')}",
                f"Build: {self.build_system.stats.get('build_time', 'N/A')}",
                f"Pacote: {self.build_system.stats.get('package_size', 'N/A')}",
                f"Total: {total_time:.2f}s"
            ]
            ui.print_info_box("Resumo da Execução", summary, Icons.CHART)
            
        except Exception as e:
            ui.print_error(f"Erro durante o setup automático: {str(e)}")
            ui.print_warning("Tente executar as etapas individualmente para diagnosticar o problema")
    
    def _check_existing_repo(self):
        """Verifica se o repositório existe e está válido"""
        ui.print_info_box("Verificando Repositório", [
            "Verificando se o diretório n8n existe...",
            "Validando estrutura do projeto..."
        ], Icons.SHIELD)
        
        if not repo_dir.exists():
            ui.print_error("Repositório N8N não encontrado!")
            ui.print_info_box("Solução", [
                "Execute 'Clonar Repositório N8N' primeiro",
                "Ou use 'Setup Completo Automático'"
            ], Icons.INFO)
            return
        
        try:
            self.build_system.check_project_structure()
            self.build_system.stats['git_cloned'] = True
            ui.print_success("Repositório válido e pronto para build!")
        except Exception as e:
            ui.print_error(f"Problema no repositório: {str(e)}")
    
    def _quick_build_only(self):
        """Executa build e package rapidamente"""
        ui.print_header("BUILD RÁPIDO", "Build + Package automatizado")
        
        if not ui.confirm("Deseja executar build + package automaticamente?"):
            ui.print_warning("Operação cancelada pelo usuário")
            return
        
        # Verifica se o repositório existe
        if not repo_dir.exists():
            ui.print_error("Repositório N8N não encontrado!")
            ui.print_info_box("Execute primeiro", [
                "'Clonar Repositório N8N' ou",
                "'Setup Completo Automático'"
            ], Icons.WARNING)
            return
        
        steps = [
            ("Executando build", self.build_system.build_project),
            ("Criando pacote", self.build_system.create_package)
        ]
        
        start_time = time.time()
        
        try:
            for i, (step_name, step_func) in enumerate(steps, 1):
                ui.print_info_box(f"Etapa {i}/{len(steps)}", [step_name], Icons.GEAR)
                step_func()
                time.sleep(0.5)
            
            total_time = time.time() - start_time
            ui.print_success(f"Build concluído em {total_time:.2f} segundos!")
            
        except Exception as e:
            ui.print_error(f"Erro durante o build: {str(e)}")
    
    def _force_reinstall_node(self):
        """Força reinstalação do Node.js"""
        if not ui.confirm("Deseja reinstalar completamente o Node.js?", danger=True):
            ui.print_warning("Operação cancelada")
            return
        
        global node_dir
        if node_dir and node_dir.exists():
            ui.show_loading("Removendo instalação anterior do Node.js")
            shutil.rmtree(node_dir, ignore_errors=True)
            ui.hide_loading()
        
        # Remove também arquivos de download
        for file_path in local_dir.glob("node-*.tar.xz"):
            file_path.unlink()
        
        ui.print_success("Instalação anterior removida")
        self.build_system.ensure_node()
    
    def _force_reinstall_pnpm(self):
        """Força reinstalação do pnpm"""
        if not ui.confirm("Deseja reinstalar completamente o pnpm?", danger=True):
            ui.print_warning("Operação cancelada")
            return
        
        pnpm_binary = bin_dir / "pnpm"
        if pnpm_binary.exists():
            pnpm_binary.unlink()
        
        ui.print_success("pnpm removido")
        self.build_system.ensure_pnpm()
    
    def _reset_repository(self):
        """Reset apenas do repositório"""
        ui.print_warning("ATENÇÃO: Esta operação irá remover o repositório N8N atual!")
        ui.print_warning("Isso inclui todos os arquivos do projeto e builds.")
        
        if not ui.confirm("Tem CERTEZA que deseja continuar?", danger=True):
            ui.print_info_box("Operação Cancelada", ["Reset não foi executado", "Repositório permanece intacto"], Icons.SHIELD)
            return
        
        ui.show_loading("Removendo repositório N8N")
        
        try:
            if repo_dir.exists():
                shutil.rmtree(repo_dir, ignore_errors=True)
            
            ui.hide_loading()
            ui.print_success("Repositório removido com sucesso!")
            ui.print_info_box("Próximos Passos", [
                "Execute 'Clonar Repositório N8N' para baixar novamente",
                "Ou use 'Setup Completo Automático'"
            ], Icons.INFO)
            
            # Reset das estatísticas relacionadas ao repositório
            self.build_system.stats['git_cloned'] = False
            self.build_system.stats['build_time'] = None
            self.build_system.stats['package_size'] = None
            self.build_system.stats['last_build'] = None
            
        except Exception as e:
            ui.hide_loading()
            ui.print_error(f"Erro durante o reset do repositório: {str(e)}")
    
    def _reset_all(self):
        """Reset completo do sistema"""
        ui.print_warning("ATENÇÃO: Esta operação irá remover TUDO!")
        ui.print_warning("Isso inclui repositório, Node.js, pnpm e todos os arquivos relacionados.")
        
        if not ui.confirm("Tem CERTEZA que deseja continuar?", danger=True):
            ui.print_info_box("Operação Cancelada", ["Reset não foi executado", "Todas as instalações permanecem intactas"], Icons.SHIELD)
            return
        
        # Confirmação dupla para operações perigosas
        if not ui.confirm("ÚLTIMA CONFIRMAÇÃO: Remover tudo mesmo?", danger=True):
            ui.print_warning("Operação cancelada na confirmação final")
            return
        
        ui.show_loading("Executando reset completo")
        
        try:
            # Remove repositório N8N completo
            if repo_dir.exists():
                shutil.rmtree(repo_dir, ignore_errors=True)
            
            # Remove pacotes gerados no diretório atual
            for zip_file in current_dir.glob("n8n*.zip"):
                zip_file.unlink()
            
            ui.hide_loading()
            ui.print_success("Reset completo executado com sucesso!")
            ui.print_info_box("Sistema Resetado", [
                "Repositório N8N foi removido completamente",
                "Todas as instalações locais foram limpas",
                "Você pode reinstalar tudo usando o menu principal"
            ], Icons.SUCCESS)
            
            # Reset completo das estatísticas
            self.build_system.stats = {
                'git_cloned': False,
                'node_version': None,
                'pnpm_version': None,
                'build_time': None,
                'package_size': None,
                'last_build': None
            }
            
        except Exception as e:
            ui.hide_loading()
            ui.print_error(f"Erro durante o reset: {str(e)}")
    
    def _system_health_check(self):
        """Executa diagnóstico completo do sistema"""
        ui.print_header("DIAGNÓSTICO DO SISTEMA", "Verificando integridade de todas as instalações")
        
        health_status = {
            "repository": {"status": "unknown", "details": ""},
            "node": {"status": "unknown", "details": ""},
            "pnpm": {"status": "unknown", "details": ""},
            "project": {"status": "unknown", "details": ""},
            "dependencies": {"status": "unknown", "details": ""}
        }
        
        ui.show_loading("Verificando repositório")
        
        # Verifica repositório
        try:
            if repo_dir.exists() and (repo_dir / "package.json").exists():
                health_status["repository"] = {"status": "healthy", "details": "Repositório N8N presente"}
            else:
                health_status["repository"] = {"status": "missing", "details": "Repositório não encontrado"}
        except Exception as e:
            health_status["repository"] = {"status": "error", "details": f"Erro: {str(e)}"}
        
        ui.hide_loading()
        ui.show_loading("Verificando Node.js")
        
        # Verifica Node.js
        try:
            if node_dir and (node_dir / "bin" / "node").exists():
                version = self.build_system.run_command(f"{node_dir / 'bin' / 'node'} --version", capture_output=True)
                health_status["node"] = {"status": "healthy", "details": f"Versão: {version}"}
            else:
                health_status["node"] = {"status": "missing", "details": "Node.js não encontrado"}
        except Exception as e:
            health_status["node"] = {"status": "error", "details": f"Erro: {str(e)}"}
        
        ui.hide_loading()
        ui.show_loading("Verificando pnpm")
        
        # Verifica pnpm
        try:
            # Tenta pnpm local primeiro
            pnpm_binary = bin_dir / "pnpm"
            if pnpm_binary.exists():
                version = self.build_system.run_command(f"{pnpm_binary} --version", capture_output=True, cwd=repo_dir)
                health_status["pnpm"] = {"status": "healthy", "details": f"Versão local: v{version}"}
            else:
                # Tenta pnpm global
                try:
                    version = self.build_system.run_command("pnpm --version", capture_output=True, cwd=repo_dir)
                    health_status["pnpm"] = {"status": "healthy", "details": f"Versão global: v{version}"}
                except:
                    health_status["pnpm"] = {"status": "missing", "details": "pnpm não encontrado"}
        except Exception as e:
            health_status["pnpm"] = {"status": "error", "details": f"Erro: {str(e)}"}
        
        ui.hide_loading()
        ui.show_loading("Verificando projeto")
        
        # Verifica estrutura do projeto
        try:
            if repo_dir.exists():
                package_json = repo_dir / "package.json"
                if package_json.exists():
                    # Verifica se é um arquivo válido
                    with open(package_json) as f:
                        json.load(f)
                    health_status["project"] = {"status": "healthy", "details": "package.json válido"}
                else:
                    health_status["project"] = {"status": "missing", "details": "package.json não encontrado"}
            else:
                health_status["project"] = {"status": "missing", "details": "Repositório não existe"}
        except Exception as e:
            health_status["project"] = {"status": "error", "details": f"Erro no package.json: {str(e)}"}
        
        ui.hide_loading()
        ui.show_loading("Verificando dependências")
        
        # Verifica dependências
        try:
            if repo_dir.exists():
                node_modules = repo_dir / "node_modules"
                if node_modules.exists() and any(node_modules.iterdir()):
                    health_status["dependencies"] = {"status": "healthy", "details": "Dependências instaladas"}
                else:
                    health_status["dependencies"] = {"status": "missing", "details": "node_modules não encontrado"}
            else:
                health_status["dependencies"] = {"status": "missing", "details": "Repositório não existe"}
        except Exception as e:
            health_status["dependencies"] = {"status": "error", "details": f"Erro: {str(e)}"}
        
        ui.hide_loading()
        
        # Mostra resultados do diagnóstico
        ui.print_header("RESULTADOS DO DIAGNÓSTICO", "Status de todos os componentes")
        
        status_icons = {
            "healthy": f"{Colors.BRIGHT_GREEN}{Icons.CHECK}",
            "missing": f"{Colors.BRIGHT_YELLOW}{Icons.WARNING}",
            "error": f"{Colors.BRIGHT_RED}{Icons.CROSS}",
            "unknown": f"{Colors.DIM}{Icons.INFO}"
        }
        
        for component, info in health_status.items():
            status = info["status"]
            details = info["details"]
            icon = status_icons.get(status, Icons.INFO)
            
            print(f"{icon} {Colors.BOLD}{component.upper():<12}{Colors.RESET} {details}")
        
        # Resumo geral
        healthy_count = sum(1 for info in health_status.values() if info["status"] == "healthy")
        total_count = len(health_status)
        
        if healthy_count == total_count:
            ui.print_success(f"Sistema totalmente saudável! ({healthy_count}/{total_count} componentes OK)")
        elif healthy_count > total_count // 2:
            ui.print_warning(f"Sistema parcialmente funcional ({healthy_count}/{total_count} componentes OK)")
        else:
            ui.print_error(f"Sistema com problemas graves ({healthy_count}/{total_count} componentes OK)")
        
        # Recomendações
        recommendations = []
        if health_status["repository"]["status"] != "healthy":
            recommendations.append("Execute 'Clonar Repositório N8N' no menu de setup")
        if health_status["node"]["status"] != "healthy":
            recommendations.append("Execute 'Instalar/Verificar Node.js' no menu de setup")
        if health_status["pnpm"]["status"] != "healthy":
            recommendations.append("Execute 'Instalar/Verificar pnpm' no menu de setup")
        if health_status["project"]["status"] != "healthy":
            recommendations.append("Verifique se o repositório foi clonado corretamente")
        if health_status["dependencies"]["status"] != "healthy":
            recommendations.append("Execute o build do projeto para instalar dependências")
        
        if recommendations:
            ui.print_info_box("Recomendações", recommendations, Icons.TARGET)
    
    def display_menu(self):
        """Exibe o menu atual"""
        category_info = {
            "main": ("MENU PRINCIPAL", "Sistema de Build e Deploy N8N"),
            "setup": ("SETUP & INSTALAÇÃO", "Ferramentas de clonagem e instalação"),
            "build": ("BUILD & PACKAGE", "Ferramentas de construção"),
            "maintenance": ("MANUTENÇÃO", "Ferramentas de limpeza e diagnóstico")
        }
        
        title, subtitle = category_info.get(self.current_category, ("MENU", ""))
        ui.print_header(title, subtitle)
        
        # Mostra status atual
        status_info = []
        if self.build_system.stats.get('git_cloned'):
            status_info.append("✓ Repositório: Clonado")
        if self.build_system.stats.get('node_version'):
            status_info.append(f"✓ Node.js: {self.build_system.stats['node_version']}")
        if self.build_system.stats.get('pnpm_version'):
            status_info.append(f"✓ pnpm: v{self.build_system.stats['pnpm_version']}")
        if self.build_system.stats.get('last_build'):
            status_info.append(f"✓ Último build: {self.build_system.stats['last_build']}")
        
        if status_info:
            ui.print_info_box("Status Atual", status_info, Icons.INFO)
        
        # Exibe itens do menu
        menu_items = self.categories[self.current_category]
        
        for i, item in enumerate(menu_items, 1):
            ui.print_menu_item(i, item)
            print()  # Espaço entre itens
        
        # Rodapé com instruções
        print(f"{Colors.DIM}{'─' * ui.width}{Colors.RESET}")
        print(f"{Colors.DIM}Digite o número da opção desejada (1-{len(menu_items)}) ou 'q' para sair{Colors.RESET}")
    
    def handle_input(self, choice: str) -> bool:
        """Processa a entrada do usuário"""
        menu_items = self.categories[self.current_category]
        
        if choice.lower() in ['q', 'quit', 'sair']:
            self._exit_program()
            return False
        
        try:
            index = int(choice) - 1
            if 0 <= index < len(menu_items):
                item = menu_items[index]
                
                # Confirmação para itens perigosos
                if item.requires_confirmation:
                    if not ui.confirm(f"Confirma a execução de '{item.title}'?", 
                                    danger=(item.danger_level == "danger")):
                        ui.print_warning("Operação cancelada")
                        return True
                
                # Executa a ação
                if item.action:
                    try:
                        ui.print_header(item.title.upper(), item.description)
                        item.action()
                        
                        if item.id not in ['back', 'exit']:
                            input(f"\n{Colors.BRIGHT_GREEN}Pressione ENTER para continuar...{Colors.RESET}")
                        
                    except KeyboardInterrupt:
                        ui.print_warning("\nOperação interrompida pelo usuário")
                        input(f"{Colors.BRIGHT_YELLOW}Pressione ENTER para continuar...{Colors.RESET}")
                    except Exception as e:
                        ui.print_error(f"Erro durante a execução: {str(e)}")
                        logger.error(f"Erro na ação {item.id}: {e}", exc_info=True)
                        input(f"{Colors.BRIGHT_RED}Pressione ENTER para continuar...{Colors.RESET}")
                
                return True
            else:
                ui.print_error("Opção inválida!")
                return True
                
        except ValueError:
            ui.print_error("Por favor, digite um número válido!")
            return True
    
    def run(self):
        """Loop principal do menu"""
        try:
            while True:
                self.display_menu()
                choice = ui.get_input("Escolha uma opção")
                
                if not choice:
                    continue
                
                if not self.handle_input(choice):
                    break
                    
        except KeyboardInterrupt:
            ui.print_warning("\n\nPrograma interrompido pelo usuário")
            self._exit_program()
        except Exception as e:
            ui.print_error(f"Erro inesperado no menu: {str(e)}")
            logger.error(f"Erro no menu principal: {e}", exc_info=True)


def check_prerequisites():
    """Verifica pré-requisitos do sistema"""
    ui.print_info_box("Verificando Pré-requisitos", [
        "Verificando se git está instalado...",
        "Verificando se sudo está disponível...",
        "Verificando conectividade de rede..."
    ], Icons.SHIELD)
    
    # Verifica git
    try:
        subprocess.run(["git", "--version"], check=True, capture_output=True)
        ui.print_success("Git está instalado")
    except (subprocess.CalledProcessError, FileNotFoundError):
        ui.print_error("Git não encontrado!")
        ui.print_info_box("Instalação do Git", [
            "Ubuntu/Debian: sudo apt install git",
            "CentOS/RHEL: sudo yum install git",
            "Fedora: sudo dnf install git"
        ], Icons.INFO)
        raise RuntimeError("Git é obrigatório para o funcionamento do script")
    
    # Verifica sudo
    try:
        subprocess.run(["sudo", "--version"], check=True, capture_output=True)
        ui.print_success("Sudo está disponível")
    except (subprocess.CalledProcessError, FileNotFoundError):
        ui.print_warning("Sudo não encontrado - algumas operações podem falhar")
    
    # Verifica conectividade básica
    try:
        urllib.request.urlopen("https://github.com", timeout=10)
        ui.print_success("Conectividade de rede OK")
    except:
        ui.print_warning("Problemas de conectividade detectados")
        ui.print_info_box("Aviso", [
            "Algumas operações podem falhar por falta de internet",
            "Verifique sua conexão de rede"
        ], Icons.WARNING)


def main():
    """Função principal com inicialização melhorada"""
    try:
        # Inicialização visual
        ui.print_header("INICIALIZANDO", "Build System N8N Ultra Moderno v3.0")
        
        # Animação de carregamento inicial
        init_steps = [
            "Verificando ambiente...",
            "Validando pré-requisitos...",
            "Carregando configurações...",
            "Preparando interface...",
            "Sistema pronto!"
        ]
        
        for step in init_steps:
            ui.show_loading(step)
            time.sleep(0.6)
            ui.hide_loading()
        
        # Verifica pré-requisitos
        check_prerequisites()
        
        # Mostra informações do sistema
        ui.print_info_box("Sistema Inicializado", [
            f"Diretório de trabalho: {current_dir}",
            f"Diretório do projeto: {repo_dir}",
            f"Python: {sys.version.split()[0]}",
            f"Sistema: {os.name}",
            f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        ], Icons.SUCCESS)
        
        time.sleep(1)
        
        # Inicializa sistema de build e menu
        build_system = BuildSystem()
        menu_manager = MenuManager(build_system)
        
        # Verifica se o repositório já existe
        if repo_dir.exists():
            ui.print_info_box("Repositório Detectado", [
                "Encontrado diretório n8n existente",
                "Você pode pular o clone e ir direto para o build"
            ], Icons.INFO)
            build_system.stats['git_cloned'] = True
        
        # Inicia o loop do menu
        menu_manager.run()
        
    except KeyboardInterrupt:
        ui.print_warning("\nPrograma interrompido pelo usuário")
        sys.exit(0)
    except Exception as e:
        ui.print_error(f"Erro crítico na inicialização: {str(e)}")
        logger.error(f"Erro crítico: {e}", exc_info=True)
        
        # Informações de debug para o usuário
        ui.print_info_box("Informações de Debug", [
            f"Erro: {str(e)}",
            f"Diretório atual: {current_dir}",
            f"Python: {sys.version}",
            "Verifique o arquivo build_script.log para mais detalhes"
        ], Icons.WARNING)
        sys.exit(1)


if __name__ == "__main__":
    main()
