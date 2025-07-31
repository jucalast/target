"""
Script para corrigir automaticamente problemas de indentação em arquivos Python.
"""
import re
import sys
from pathlib import Path

def fix_file_indentation(file_path):
    """Corrige a indentação de um arquivo Python."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        in_class = False
        in_def = False
        in_docstring = False
        indent_stack = [0]
        new_lines = []
        
        for i, line in enumerate(lines):
            stripped = line.strip()
            
            # Verifica se estamos em uma docstring
            if stripped.startswith('"""') or stripped.startswith("'''"):
                in_docstring = not in_docstring
                new_lines.append(line)
                continue
                
            if in_docstring:
                new_lines.append(line)
                continue
                
            # Remove espaços em branco no final da linha
            clean_line = line.rstrip() + '\n'
            
            # Verifica se é uma definição de classe
            if line.strip().startswith('class '):
                in_class = True
                indent = len(line) - len(line.lstrip())
                indent_stack = [indent]
                new_lines.append(clean_line)
                continue
                
            # Verifica se é uma definição de função
            if line.strip().startswith('def '):
                in_def = True
                indent = len(line) - len(line.lstrip())
                if indent > indent_stack[-1]:
                    indent_stack.append(indent)
                new_lines.append(clean_line)
                continue
                
            # Verifica se a linha não está vazia
            if stripped:
                current_indent = len(line) - len(line.lstrip())
                
                # Se a indentação atual for menor que a esperada, ajusta
                if current_indent < indent_stack[-1]:
                    clean_line = ' ' * indent_stack[-1] + line.lstrip()
                # Se for um bloco de código dentro de uma classe ou função
                elif current_indent <= indent_stack[-1] + 4 and (in_class or in_def):
                    clean_line = ' ' * (indent_stack[-1] + 4) + line.lstrip()
                
                new_lines.append(clean_line)
            else:
                new_lines.append('\n')
        
        # Escreve as correções de volta para o arquivo
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
            
        print(f"Arquivo corrigido: {file_path}")
        return True
        
    except Exception as e:
        print(f"Erro ao processar {file_path}: {str(e)}")
        return False

def find_python_files(directory):
    """Encontra todos os arquivos Python no diretório especificado."""
    path = Path(directory)
    return list(path.rglob("*.py"))

def main():
    if len(sys.argv) != 2:
        print("Uso: python fix_indentation.py <diretório>")
        sys.exit(1)
    
    directory = sys.argv[1]
    python_files = find_python_files(directory)
    
    print(f"Encontrados {len(python_files)} arquivos Python em {directory}")
    
    success = 0
    for file_path in python_files:
        if fix_file_indentation(str(file_path)):
            success += 1
    
    print(f"\nCorreção concluída! {success}/{len(python_files)} arquivos processados com sucesso.")

if __name__ == "__main__":
    main()
