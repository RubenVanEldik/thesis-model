# Build the Docker container
docker build . -t thesis-model -f cli.Dockerfile

# Run the Docker container
docker run -i -t -p=8080:8080 -v=$PWD/gurobi.lic:/opt/gurobi/gurobi.lic:ro thesis-model

# Export the Docker container
docker create thesis-model --name thesis-model-container
docker export thesis-model-container > thesis-model.tar
