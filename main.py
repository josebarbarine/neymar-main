from typing import Optional
from fastapi import FastAPI, HTTPException, status, Response
from pydantic import BaseModel, Field
import uvicorn

app = FastAPI(title="API de Produtos - Exercícios Práticos")

produtos_db = {
    1: {"nome": "Teclado", "preco": 100.0, "estoque": 10, "em_estoque": True, "ativo": True},
    2: {"nome": "Mouse", "preco": 50.0, "estoque": 5, "em_estoque": False, "ativo": True}
}


class ProdutoSchema(BaseModel):
    nome: str
    preco: float = Field(gt=0, description="O preço deve ser maior que zero")
    estoque: int = Field(ge=0, description="O estoque não pode ser negativo")
    # Exercício 2: Valor padrão para demonstrar o perigo do PUT
    em_estoque: bool = True 
    # Exercício 4: Base para o Soft Delete
    ativo: bool = True 

class ProdutoPatchSchema(BaseModel):
    nome: Optional[str] = None
    preco: Optional[float] = Field(None, gt=0)
    estoque: Optional[int] = Field(None, ge=0)
    em_estoque: Optional[bool] = None
    ativo: Optional[bool] = None


@app.post("/produtos/", status_code=status.HTTP_201_CREATED)
def criar_produto(produto: ProdutoSchema):
    # As validações do Field já garantem que preco > 0 e estoque >= 0
    novo_id = max(produtos_db.keys()) + 1 if produtos_db else 1
    produtos_db[novo_id] = produto.model_dump()
    return {"id": novo_id, **produtos_db[novo_id]}


@app.put("/produtos/perigoso/{produto_id}")
def atualizar_produto_perigoso(produto_id: int, produto: ProdutoSchema):
    if produto_id not in produtos_db:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    
 
    produtos_db[produto_id] = produto.model_dump()
    return {
        "mensagem": "Substituição perigosa concluída. Verifique o estado do campo 'em_estoque'.",
        "produto": produtos_db[produto_id]
    }


@app.patch("/produtos/{produto_id}")
def atualizar_produto_parcial(produto_id: int, produto_atualizacao: ProdutoPatchSchema):
    if produto_id not in produtos_db:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    
    produto_atual = produtos_db[produto_id]
    
    if produto_atualizacao.preco is not None:
        if produto_atualizacao.preco < (produto_atual["preco"] * 0.5):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="O novo preço não pode ser inferior a 50% do preço atual."
            )
            
    dados_atualizados = produto_atualizacao.model_dump(exclude_unset=True)
    produto_atual.update(dados_atualizados)
    
    produtos_db[produto_id] = produto_atual
    return {"mensagem": "Produto atualizado com sucesso.", "produto": produto_atual}


@app.delete("/produtos/{produto_id}/soft")
def soft_delete_produto(produto_id: int):
    if produto_id not in produtos_db:
        raise HTTPException(status_code=404, detail="Produto não encontrado.")
    
    # Altera o estado lógico em vez de usar `del produtos_db[produto_id]`
    produtos_db[produto_id]["ativo"] = False
    return {"mensagem": "O produto foi desativado com sucesso (Soft Delete)."}


@app.put("/produtos/{produto_id}")
def upsert_produto(produto_id: int, produto: ProdutoSchema, response: Response):
    # Comportamento duplo: Atualiza se existir, Cria se não existir
    if produto_id in produtos_db:
        produtos_db[produto_id] = produto.model_dump()
        response.status_code = status.HTTP_200_OK # Atualização bem-sucedida
        return {"mensagem": "Produto atualizado.", "produto": produtos_db[produto_id]}
    else:
        produtos_db[produto_id] = produto.model_dump()
        response.status_code = status.HTTP_201_CREATED # Criação bem-sucedida
        return {"mensagem": "Produto criado do zero.", "produto": produtos_db[produto_id]}


# Inicializador do Uvicorn para rodar o arquivo diretamente
if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)