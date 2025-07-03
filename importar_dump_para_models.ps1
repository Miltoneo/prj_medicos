# Caminho do arquivo .sql
$sqlFile = "dump_dados_ajustado_para_models.sql"

# Lê o conteúdo completo do script SQL
$sqlContent = Get-Content $sqlFile -Raw

# Executa o conteúdo dentro do container Docker (mysql_c)
docker exec -i mysql_c mysql -uroot -proot prd_milenio --execute="$sqlContent"

Write-Host "✅ Script SQL executado com sucesso no banco de dados 'prd_milenio' dentro do container 'mysql_c'."