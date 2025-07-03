#!/bin/bash

# Caminho do arquivo de versão
VERSION_FILE="core/version.txt"

# Lê a versão
if [ ! -f "$VERSION_FILE" ]; then
  echo "❌ Arquivo $VERSION_FILE não encontrado."
  exit 1
fi

VERSION=$(cat "$VERSION_FILE" | tr -d '[:space:]')

if [ -z "$VERSION" ]; then
  echo "❌ Versão inválida ou vazia no arquivo $VERSION_FILE"
  exit 1
fi

# Nome da imagem local e no Docker Hub
IMAGE_NAME="medicos"
REMOTE_IMAGE="miltoneo/$IMAGE_NAME"

echo "🔨 Construindo imagem local: $IMAGE_NAME:$VERSION"
docker build -t $IMAGE_NAME:$VERSION .

# Tag para Docker Hub
docker tag $IMAGE_NAME:$VERSION $REMOTE_IMAGE:$VERSION
docker tag $IMAGE_NAME:$VERSION $REMOTE_IMAGE:latest

echo "✅ Imagens locais e remotas com tags criadas:"
docker images | grep "$IMAGE_NAME"

# Verifica se usuário está logado no Docker Hub
if ! docker info | grep -q "Username: miltoneo"; then
  echo "⚠️  Você precisa fazer login no Docker Hub:"
  echo "    docker login"
  exit 1
fi

# Push para Docker Hub
echo "📤 Enviando imagem para Docker Hub..."
docker push $REMOTE_IMAGE:$VERSION
docker push $REMOTE_IMAGE:latest

echo "✅ Push completo!"
echo "🔗 https://hub.docker.com/r/miltoneo/medicos/tags"
