#!/bin/bash

# Configurações do banco de dados
DATABASE_HOST="onkoto.com.br"
DATABASE_NAME="db_medicos"
DATABASE_USER="admin"
DATABASE_PASSWORD="admin"
DATABASE_PORT="5432"

# Nome do contêiner Docker do PostgreSQL
DOCKER_CONTAINER_NAME="pgsql_c"

# Diretório para armazenar os backups
BACKUP_DIR="/var/backups/postgresql"

# Nome do arquivo de backup (com timestamp)
BACKUP_FILE="$BACKUP_DIR/db_medicos_$(date +%Y%m%d_%H%M%S).backup"

# Garantir que o diretório de backup existe
mkdir -p "$BACKUP_DIR"

# Executar o backup dentro do contêiner Docker no formato custom
sudo docker exec "$DOCKER_CONTAINER_NAME" bash -c "export PGPASSWORD='$DATABASE_PASSWORD'; pg_dump -h '$DATABASE_HOST' -U '$DATABASE_USER' -p '$DATABASE_PORT' -F c '$DATABASE_NAME'" > "$BACKUP_FILE"

# Verificar se o backup foi bem-sucedido
if [ $? -eq 0 ]; then
    echo "Backup realizado com sucesso: $BACKUP_FILE"
else
    echo "Erro ao realizar o backup do banco de dados." >&2
    exit 1
fi

# Remover backups antigos (mais de 7 dias)
find "$BACKUP_DIR" -type f -name "*.backup" -mtime +7 -exec rm {} \;