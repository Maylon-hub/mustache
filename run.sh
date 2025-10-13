#!/bin/bash
export COMPOSE_PROJECT_NAME=mustache
export MUSTACHE_WORKSPACE=/home/Documents/datasets
docker-compose up -d
sleep 3
