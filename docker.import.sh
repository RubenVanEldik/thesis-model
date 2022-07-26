zcat thesis-model.tar.gz | docker import -c "WORKDIR /app" -c "CMD streamlit run Introduction.py" - thesis-model
