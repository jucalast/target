#!/usr/bin/env python3
"""
Script para corrigir automaticamente problemas comuns do Flake8 em arquivos Python.

Funcionalidades:
1. Remove imports não utilizados (F401)
2. Corrige linhas muito longas (E501)
3. Remove linhas em branco extras (E303, E305, E304)
4. Remove espaços em branco no final das linhas (W291, W293)
5. Adiciona linhas em branco faltando (E302, E305)
"""

import ast
import os
import re
import sys
from pathlib import Path
from typing import List, Set, Tuple

class Flake8Fixer:
    def __init__(self, file_path: str):
        self.file_path = file_path
        self.lines = []
        self.modified = False

    def fix_issues(self) -> bool:
        """Corrige os problemas no arquivo e retorna True se houve alterações."""
        if not os.path.exists(self.file_path):
            print(f"Arquivo não encontrado: {self.file_path}")
            return False

        # Lê o conteúdo do arquivo
        with open(self.file_path, 'r', encoding='utf-8') as f:
            self.lines = f.readlines()

        # Aplica as correções
        original_lines = self.lines.copy()
        
        self.fix_unused_imports()
        self.fix_line_length()
        self.fix_blank_lines()
        self.fix_trailing_whitespace()
        self.ensure_newline_at_eof()

        # Verifica se houve alterações
        if self.lines != original_lines:
            self.modified = True
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.writelines(self.lines)
            print(f"✅ Corrigido: {self.file_path}")
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

    def fix_line_length(self, max_length: int = 79):
        """Quebra linhas muito longas (E501)."""
        for i, line in enumerate(self.lines):
            # Pula strings de documentação e comentários
            if line.lstrip().startswith(('#', '"""', "'''")):
                continue
                
            if len(line.rstrip('\n')) > max_length:
                # Tenta quebrar a linha em um operador
                for op in [',', '(', ')', '{', '}', '=', '+', '-', '*', '/', ' and ', ' or ']:
                    if op in line:
                        parts = line.split(op)
                        if len(parts) > 1:
                            # Encontra o melhor lugar para quebrar
                            for j in range(len(parts)-1, 0, -1):
                                left = op.join(parts[:j])
                                if len(left) <= max_length:
                                    # Adiciona o operador de volta e quebra a linha
                                    new_line = left + op + '\\\n'
                                    # Calcula a indentação da linha atual
                                    indent = ' ' * (len(line) - len(line.lstrip()))
                                    
                                    # Adiciona a continuação na próxima linha com indentação extra
                                    next_line = indent + '    ' + op.join(parts[j:]).lstrip()
                                    
                                    # Substitui as linhas
                                    self.lines[i] = new_line
                                    self.lines.insert(i+1, next_line)
                                    self.modified = True
                                    break
                            break

    def fix_blank_lines(self):
        """Corrige problemas com linhas em branco (E302, E303, E304, E305)."""
        new_lines = []
        blank_lines = 0
        in_function = False
        
        for line in self.lines:
            stripped = line.strip()
            
            # Conta linhas em branco consecutivas
            if not stripped:
                blank_lines += 1
                continue
                
            # Se for início de função/classe, garante 2 linhas em branco antes
            if stripped.startswith(('def ', 'class ')) and not in_function:
                # Remove linhas em branco extras
                while len(new_lines) > 0 and not new_lines[-1].strip():
                    new_lines.pop()
                # Adiciona 2 linhas em branco
                new_lines.extend(['\n', '\n'])
                in_function = True
            # Se for dentro de uma função, garante apenas 1 linha em branco
            elif in_function and blank_lines > 1:
                new_lines.append('\n')
                blank_lines = 0
            # Se for fora de função, adiciona as linhas em branco (até 2)
            elif not in_function and blank_lines > 0:
                new_lines.extend(['\n'] * min(2, blank_lines))
                blank_lines = 0
                
            # Adiciona a linha atual
            new_lines.append(line)
            
            # Reseta o contador de linhas em branco
            blank_lines = 0
            
            # Verifica se estamos dentro de uma função
            if stripped.endswith(':'):
                in_function = True
            elif stripped == 'pass':
                in_function = False
        
        self.lines = new_lines
        self.modified = self.modified or (self.lines != new_lines)

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
