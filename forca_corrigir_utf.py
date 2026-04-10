entrada = "dados.csv"
saida = "dados_corrigidos.csv"

# Substituições comuns de erros de encoding
substituicoes = {
    "Ã§": "ç",
    "Ã£": "ã",
    "Ã¡": "á",
    "Ã©": "é",
    "Ãª": "ê",
    "Ã³": "ó",
    "Ãº": "ú",
    "Ã": "â",
    "â€œ": "“",
    "â€": "”",
    "â€˜": "‘",
    "â€™": "’",
    "â€“": "–",
    "â€”": "—",
    "Â": "",  # geralmente lixo residual
    "çÃ£o": "ção",
    "Ã³": "ó"
}

with open(entrada, "r", encoding="utf-8-sig") as f:
    texto = f.read()

for errado, certo in substituicoes.items():
    texto = texto.replace(errado, certo)

with open(saida, "w", encoding="utf-8") as f:
    f.write(texto)

print("Substituições aplicadas e arquivo corrigido salvo como:", saida)
