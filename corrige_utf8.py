# Corrige texto mal interpretado como Latin-1 mas salvo como UTF-8

input_file = "dados.csv"
output_file = "corrigido.csv"

with open(input_file, "r", encoding="utf-8-sig") as f:
    conteudo = f.read()

# Reverte os caracteres interpretados como Latin-1, voltando ao original UTF-8
corrigido = conteudo.encode("latin1").decode("utf-8")

with open(output_file, "w", encoding="utf-8") as f:
    f.write(corrigido)

print("Arquivo corrigido salvo como:", output_file)
