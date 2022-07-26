zcat thesis-model.tar.gz | docker import --change "CMD cd app; streamlit run Introduction.py" - thesis-model
