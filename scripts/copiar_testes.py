# Script para copiar todos os arquivos de teste para a pasta scripts
import shutil
import os

src_folder = os.getcwd()
dst_folder = os.path.join(src_folder, 'scripts')

os.makedirs(dst_folder, exist_ok=True)

for filename in os.listdir(src_folder):
    if filename.startswith('test') and filename.endswith('.py'):
        src_file = os.path.join(src_folder, filename)
        dst_file = os.path.join(dst_folder, filename)
        shutil.copy2(src_file, dst_file)
        print(f'Copiado: {filename} para scripts/')
