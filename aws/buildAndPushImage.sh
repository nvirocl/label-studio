#!/usr/bin/env bash

source .env

# obtener la versión desde el 1er comando, si no desde package.json
if [ -n "$1" ]; then
  image_tag=$1
else
  image_tag=$(node -p "require('./package.json').version")
fi
repo_name=$REPOSITORY_NAME
ecr_repo=443073691211.dkr.ecr.us-west-2.amazonaws.com/$repo_name

cd ..
docker buildx build --secret id=npm_token,env=NPM_TOKEN -t $repo_name:v$image_tag -t $ecr_repo:v$image_tag --load .
aws ecr get-login-password --region us-west-2 | docker login --username AWS --password-stdin 443073691211.dkr.ecr.us-west-2.amazonaws.com
docker push $ecr_repo:v$image_tag
