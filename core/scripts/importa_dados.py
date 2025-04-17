import requests
import pandas as pd

API_URL = (
    "https://dadosabertos.aneel.gov.br/api/3/action/datastore_search"
)
RESOURCE_ID = "11ec447d-698d-4ab8-977f-b424d5deee6a"

def fetch_records(limit=1000, q=None):
    """
    Busca até ‘limit’ registros por página, opcionalmente filtrando 
    com a string de query ‘q’. Retorna um DataFrame do pandas.
    """
    offset = 0
    all_docs = []

    while True:
        params = {
            "resource_id": RESOURCE_ID,
            "limit": limit,
            "offset": offset,
        }
        if q:
            params["q"] = q

        resp = requests.get(API_URL, params=params)
        resp.raise_for_status()
        data = resp.json()["result"]

        docs = data["records"]
        if not docs:
            break

        all_docs.extend(docs)
        offset += limit
        # se chegou ao fim
        if offset >= data["total"]:
            break

    # Transforma lista de dicts em DataFrame
    df = pd.DataFrame(all_docs)
    return df

if __name__ == "__main__":
    # Exemplo: buscar as 5 primeiras usinas cujo nome contenha “jones”
    df_jones = fetch_records(limit=5, q="title:jones")
    print(df_jones.head())
