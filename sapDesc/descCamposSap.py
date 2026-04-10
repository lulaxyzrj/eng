import requests
from bs4 import BeautifulSoup
from deep_translator import GoogleTranslator
import time

def extrair_descricao(html):
    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", class_="ddic-overview")
    if not table:
        return None
    for row in table.find_all("tr"):
        cols = row.find_all("td")
        if len(cols) >= 2 and "short description" in cols[0].text.strip().lower():
            return cols[1].text.strip()
    return None

def buscar_descricao_sap(campo_sap):
    headers = {"User-Agent": "Mozilla/5.0"}
    urls = [
        f"https://www.sapdatasheet.org/abap/elem/{campo_sap.lower()}.html",
        f"https://www.sapdatasheet.org/abap/dtel/{campo_sap.lower()}.html"
    ]

    for url in urls:
        try:
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                continue

            descricao_en = extrair_descricao(response.text)
            if descricao_en:
                descricao_pt = GoogleTranslator(source='auto', target='pt').translate(descricao_en)
                return campo_sap, descricao_pt
        except Exception as e:
            return campo_sap, f"Erro: {str(e)}"

    return campo_sap, "Descrição não encontrada"

# Teste
campos = ["aedat", "adrnr", "abkrs", "abcin", "abgrs", "blart", "belnr"]

print("Campo | Descrição em Português")
print("-" * 60)
for campo in campos:
    nome, desc = buscar_descricao_sap(campo)
    print(f"{nome} | {desc}")
    time.sleep(2)
