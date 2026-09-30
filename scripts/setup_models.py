from backend.config import Settings
from backend.vectors import Embeddings

if __name__=='__main__':
    model=Embeddings(Settings(),download=True)
    print(f'Local model cached: {model.name}, {model.dimension} dimensions')
