<<<<<<< Updated upstream
#!/bin/bash
docker compose up --build -d
echo "MustaCHE v2 is starting..."
echo "Access the application at: http://localhost:5001"
=======
export COMPOSE_PROJECT_NAME=mustache
export MUSTACHE_WORKSPACE=/home/guest/workspace
docker-compose up -d
sleep 3
>>>>>>> Stashed changes
