import subprocess
import sys

# Execute o limpar cache script
result = subprocess.run([sys.executable, "limpar_cache.py"], 
                       capture_output=True, text=True, cwd=".")

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")
import sys

# Execute o debug script
result = subprocess.run([sys.executable, "debug_pis.py"], 
                       capture_output=True, text=True, cwd=".")

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print(f"\nReturn code: {result.returncode}")
