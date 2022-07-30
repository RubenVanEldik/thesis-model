cd ..
docker run -p=8501:8501 -v=$PWD/gurobi.lic:/opt/gurobi/gurobi.lic:ro --name thesis-model-container thesis-model
