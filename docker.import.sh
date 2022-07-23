zcat thesis-model.tar.gz | docker import --change 'CMD ["streamlit", "run", "Introduction.py", "--server.address", "0.0.0.0", "--server.port", "8080"]' - thesis-model
