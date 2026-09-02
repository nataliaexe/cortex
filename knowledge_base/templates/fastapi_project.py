"""
Template para projeto FastAPI
Projeto web moderno com Python
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List
import uvicorn

app = FastAPI(
    title="API Projeto",
    description="API criada com Gênesis Córtex",
    version="1.0.0"
)

# Configuração CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de dados
class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: float

# Rotas
@app.get("/")
async def root():
    return {"message": "API funcionando"}

@app.get("/items", response_model=List[Item])
async def get_items():
    """Retorna todos os itens"""
    return []

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    """Retorna um item específico"""
    return Item(id=item_id, name="Exemplo", price=9.99)

@app.post("/items", response_model=Item)
async def create_item(item: Item):
    """Cria um novo item"""
    return item

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: Item):
    """Atualiza um item"""
    item.id = item_id
    return item

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Deleta um item"""
    return {"message": f"Item {item_id} deletado"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)