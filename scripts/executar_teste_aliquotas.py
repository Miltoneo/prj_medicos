import subprocess
import sys

result = subprocess.run([sys.executable, "teste_aliquotas.py"], 
                       capture_output=True, text=True, cwd=".")

print("SAÍDA:")
print(result.stdout)
if result.stderr:
    print("\nERROS:")
    print(result.stderr)
print(f"\nCódigo de retorno: {result.returncode}")
