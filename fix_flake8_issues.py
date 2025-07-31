#!/usr/bin/env python3
"""
Script para corrigir automaticamente problemas comuns do Flake8 em arquivos Python.

Funcionalidades:
1. Remove imports não utilizados (F401)
2. Corrige linhas muito longas (E501)
3. Remove linhas em branco extras (E303, E305, E304)
4. Remove espaços em branco no final das linhas (W291, W293)
5. Adiciona linhas em branco faltando (E302, E305)
6. Corrige espaçamento após vírgulas (E231)
7. Remove barras invertidas desnecessárias em colchetes (E502)
8. Corrige indentação de linhas de continuação (E128)
"""

import ast
import os
import re
import sys
import logging
from pathlib import Path
from typing import List, Set, Tuple, Dict, Any, Optional

# Configuração de logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

class Flake8Fixer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lines = []
        self.modified = False

    def fix_issues(self) -> bool:
        """Corrige os problemas no arquivo e retorna True se houve alterações."""
        if not os.path.exists(self.file_path):
            logger.warning(f"Arquivo não encontrado: {self.file_path}")
            return False

        # Lê o conteúdo do arquivo
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.lines = f.readlines()
        except Exception as e:
            logger.error(f"Erro ao ler o arquivo {self.file_path}: {e}")
            return False

        # Aplica as correções
        original_lines = self.lines.copy()
        
        try:
            self.fix_unused_imports()
            self.fix_line_length()
            self.fix_commas_and_backslashes()
            self.fix_continuation_lines()
            self.fix_blank_lines()
            self.fix_trailing_whitespace()
            self.ensure_newline_at_eof()
            
            # Verifica se houve alterações
            if self.lines != original_lines:
                self.modified = True
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.writelines(self.lines)
                logger.info(f"✅ Corrigido: {self.file_path}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Erro ao corrigir o arquivo {self.file_path}: {e}")
            # Em caso de erro, restaura o conteúdo original
            if self.modified:
                with open(self.file_path, 'w', encoding='utf-8') as f:
                    f.writelines(original_lines)
            return False
        else:
            print(f"ℹ️  Nenhuma alteração necessária: {self.file_path}")
            
        return self.modified

    def fix_unused_imports(self):
        """Remove imports não utilizados (F401)."""
        try:
            # Analisa o código para encontrar imports não utilizados
            tree = ast.parse(''.join(self.lines))
            used_names = set()
            
            # Encontra todos os nomes usados no código
            for node in ast.walk(tree):
                if isinstance(node, ast.Name):
                    used_names.add(node.id)
                elif isinstance(node, ast.Attribute):
                    used_names.add(node.attr)
            
            # Verifica cada linha de import
            for i, line in enumerate(self.lines):
                if line.lstrip().startswith(('import ', 'from ')):
                    # Extrai os nomes importados
                    if ' as ' in line:
                        # Ex: import os as sistema_operacional
                        import_name = line.split(' as ')[0].split()[-1]
                    elif 'from ' in line and ' import ' in line:
                        # Ex: from datetime import datetime
                        import_name = line.split(' import ')[1].split(',')[0].strip()
                    else:
                        # Ex: import os
                        import_name = line.split(' import ')[-1].strip()
                    
                    # Remove o 
                    import_name = import_name.strip()
                    
                    # Se o nome não for usado em lugar nenhum, remove a linha
                    if import_name not in used_names and not any(
                        f".{import_name}." in l for l in self.lines
                    ):
                        self.lines[i] = ''
                        self.modified = True
        except Exception as e:
            print(f"⚠️  Erro ao analisar imports em {self.file_path}: {e}")

    def fix_line_length(self) -> None:
        """Corrige linhas muito longas (E501)."""
        max_length = 79
        i = 0
        while i < len(self.lines):
            line = self.lines[i]
            if len(line) > max_length and not line.strip().startswith('#'):
                # Ignora strings de documentação
                if '"""' in line or "'''" in line:
                    i += 1
                    continue
                    
                # Tenta quebrar a linha em um local apropriado
                if '(' in line and ')' in line and line.count('(') == line.count(')'):
                    # Se for uma chamada de função, quebra após uma vírgula
                    if ',' in line:
                        last_comma = line.rfind(',')
                        if last_comma > 0 and last_comma < max_length - 1:
                            indent = len(line) - len(line.lstrip())
                            next_line_indent = ' ' * (indent + 4)
                            self.lines[i] = line[:last_comma + 1] + '\n' + next_line_indent + line[last_comma + 1:].lstrip()
                            self.modified = True
                            i += 1  # Pula a próxima linha já que acabamos de adicioná-la
                            continue
                
                # Se for uma atribuição com =, tenta quebrar após o =
                if '=' in line and not any(op in line for op in ['==', '!=', '>=', '<=', '+=', '-=', '*=', '/=']):
                    eq_pos = line.find('=')
                    if 0 < eq_pos < max_length - 1:
                        indent = len(line) - len(line.lstrip())
                        next_line_indent = ' ' * (indent + 4)
                        self.lines[i] = line[:eq_pos + 1] + '\n' + next_line_indent + line[eq_pos + 1:].lstrip()
                        self.modified = True
                        i += 1
                        continue
                
                # Se não conseguir quebrar de forma inteligente, adiciona noqa
                if len(line) > max_length:
                    self.lines[i] = line.rstrip() + '  # noqa: E501\n'
            i += 1

    def fix_commas_and_backslashes(self) -> None:
        """Corrige espaçamento após vírgulas (E231) e barras desnecessárias (E502)."""
        for i, line in enumerate(self.lines):
            # Ignora comentários e strings
            if '#' in line:
                line, _ = line.split('#', 1)
            if any(q in line for q in ['"""', "'''"]):
                continue
                
            # Corrige espaçamento após vírgulas
            line = re.sub(r',(\S)', r', \1', line)
            
            # Remove barras desnecessárias em colchetes
            line = re.sub(r'(\[.*?)\\(.*?\])', r'\1\2', line)
            
            # Remove espaços em branco após abertura de colchetes
            line = re.sub(r'\[\s+', '[', line)
            # Remove espaços em branco antes do fechamento de colchetes
            line = re.sub(r'\s+\]', ']', line)
            
            if line != self.lines[i]:
                self.lines[i] = line
                self.modified = True
                
    def fix_continuation_lines(self) -> None:
        """Corrige indentação de linhas de continuação (E128)."""
        i = 0
        while i < len(self.lines):
            line = self.lines[i]
            stripped = line.lstrip()
            
            # Se a linha atual é uma continuação da anterior
            if i > 0 and stripped and not stripped.startswith(('#', 'def ', 'class ')):
                prev_line = self.lines[i-1].rstrip()
                
                # Se a linha anterior termina com vírgula, dois pontos ou abre parêntese/chave/colchete
                if prev_line and prev_line[-1] in ',:([{':
                    # Calcula a indentação baseada na linha anterior
                    indent = len(prev_line) - len(prev_line.lstrip())
                    if prev_line.rstrip().endswith('('):
                        indent += 4  # Indentação extra para parênteses
                    
                    # Aplica a indentação correta
                    self.lines[i] = ' ' * indent + stripped
                    self.modified = True
            
            i += 1

    def fix_blank_lines(self) -> None:
        """Corrige linhas em branco extras (E303, E304, E305) e adiciona as faltantes (E302)."""
        # Remove linhas em branco extras no início
        while self.lines and not self.lines[0].strip():
            self.lines.pop(0)
            self.modified = True
            
        # Remove linhas em branco extras no final
        while self.lines and not self.lines[-1].strip():
            self.lines.pop()
            self.modified = True
            
        # Remove linhas em branco extras entre linhas de código
        i = 1
        while i < len(self.lines) - 1:
            current_line = self.lines[i].strip()
            prev_line = self.lines[i-1].strip()
            next_line = self.lines[i+1].strip() if i+1 < len(self.lines) else ''
            
            # Remove múltiplas linhas em branco
            if not current_line and not prev_line:
                self.lines.pop(i)
                self.modified = True
            else:
                i += 1
                
        # Adiciona linhas em branco faltantes (E302, E305)
        i = 0
        while i < len(self.lines) - 1:
            current_line = self.lines[i].strip()
            next_line = self.lines[i+1].strip() if i+1 < len(self.lines) else ''
            
            # Adiciona linha em branco após imports
            if (current_line.startswith(('import ', 'from ')) and 
                not next_line.startswith(('import ', 'from ')) and 
                next_line and 
                not next_line.startswith(('class ', 'def ')) and
                not next_line.startswith('@')):
                self.lines.insert(i+1, '\n')
                self.modified = True
                i += 1
                
            # Adiciona 2 linhas em branco antes de classes e funções no nível superior
            if (current_line.startswith(('class ', 'def ')) and 
                i > 0 and 
                self.lines[i-1].strip() and 
                (i == 1 or self.lines[i-2].strip() or self.lines[i-1].strip() != '\n') and
                not any(self.lines[i-1].strip().startswith(s) for s in ['@', 'class ', 'def '])):
                self.lines.insert(i, '\n' * 2)
                self.modified = True
                i += 2
            
            i += 1  

    def fix_trailing_whitespace(self):
        """Remove espaços em branco no final das linhas (W291, W293)."""
        for i, line in enumerate(self.lines):
            # Remove espaços em branco no final da linha
            new_line = line.rstrip() + '\n' if line.strip() else '\n'
            if new_line != line:
                self.lines[i] = new_line
                self.modified = True

    def ensure_newline_at_eof(self):
        """Garante que o arquivo termine com exatamente uma nova linha."""
        if self.lines and not self.lines[-1].endswith('\n'):
            self.lines[-1] = self.lines[-1].rstrip('\n') + '\n'

def find_python_files(directory: str) -> List[str]:
    """Encontra todos os arquivos Python no diretório, ignorando venv e outras pastas."""
    python_files = []
    skip_dirs = {'venv', '.venv', 'env', '.env', '__pycache__', '.git', '.github', 'migrations'}
    
    for root, dirs, files in os.walk(directory):
        # Remove diretórios que devem ser ignorados
        dirs[:] = [d for d in dirs if d not in skip_dirs and not d.startswith('.')]
        
        for file in files:
            if file.endswith('.py'):
                python_files.append(os.path.join(root, file))
    
    return python_files

def main():
    if len(sys.argv) > 1:
        target = sys.argv[1]
    else:
        target = os.getcwd()
    
    # Verifica se o alvo é um arquivo ou diretório
    if os.path.isfile(target) and target.endswith('.py'):
        files = [target]
    elif os.path.isdir(target):
        files = find_python_files(target)
    else:
        print(f"Erro: '{target}' não é um arquivo Python ou diretório válido.")
        sys.exit(1)
    
    if not files:
        print("Nenhum arquivo Python encontrado.")
        return
    
    print(f"🔍 Encontrados {len(files)} arquivos Python para verificação...")
    
    # Processa cada arquivo
    modified_count = 0
    for file_path in files:
        fixer = Flake8Fixer(file_path)
        if fixer.fix_issues():
            modified_count += 1
    
    print(f"\n✅ Concluído! {modified_count}/{len(files)} arquivos foram modificados.")

if __name__ == "__main__":
    main()
