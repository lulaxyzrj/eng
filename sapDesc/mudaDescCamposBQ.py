import pandas as pd
from google.cloud import bigquery

def atualizar_descricao_bq_com_records(csv_path: str, project_id: str):
    client = bigquery.Client(project=project_id)
    df = pd.read_csv(csv_path)

    # Agrupar por dataset e tabela
    for (dataset_id, table_id), grupo in df.groupby(["dataset_id", "table_id"]):
        table_ref = f"{project_id}.{dataset_id}.{table_id}"
        print(f"🔧 Atualizando: {table_ref}")
        tabela = client.get_table(table_ref)
        schema = tabela.schema

        # Transforma o schema original com novas descrições
        def atualizar_schema(campos, prefix=""):
            novos_campos = []
            for campo in campos:
                caminho_completo = f"{prefix}.{campo.name}" if prefix else campo.name
                # Busca descrição no CSV
                linha = grupo[grupo['column_path'] == caminho_completo]
                nova_desc = linha['description'].values[0] if not linha.empty else campo.description

                # Recursivamente processa RECORDs
                if campo.field_type == "RECORD":
                    subcampos = atualizar_schema(campo.fields, caminho_completo)
                else:
                    subcampos = campo.fields

                campo_atualizado = bigquery.SchemaField(
                    name=campo.name,
                    field_type=campo.field_type,
                    mode=campo.mode,
                    description=nova_desc,
                    fields=subcampos
                )
                novos_campos.append(campo_atualizado)
            return novos_campos

        novo_schema = atualizar_schema(schema)
        tabela.schema = novo_schema
        client.update_table(tabela, ["schema"])
        print(f"✅ Descrições atualizadas com sucesso para {table_ref}\n")

# Exemplo de uso
if __name__ == "__main__":
    atualizar_descricao_bq_com_records("descriptions.csv", "seu-projeto-gcp")
