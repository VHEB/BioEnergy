from django.core.management.base import BaseCommand
from core.models import Usina  # ajuste se estiver em outro lugar
from core.scripts.importa_dados import fetch_records
import pandas as pd

class Command(BaseCommand):
    help = 'Importa dados de usinas da API da ANEEL e salva no banco de dados'

    def handle(self, *args, **kwargs):
        self.stdout.write("Buscando dados da API...")
        df = fetch_records(limit=500)

        self.stdout.write(f"{len(df)} registros encontrados.")
        
        # Limpa a tabela antes de inserir (opcional, cuidado!)
        Usina.objects.all().delete()

        # Mapeando colunas do dataframe para os campos do modelo
        for _, row in df.iterrows():
            try:
                Usina.objects.create(
                    nome=row.get('empreendimento', '')[:255],
                    estado=row.get('sigla_uf', ''),
                    fonte=row.get('fonte', ''),
                    potencia_kw=row.get('potencia_kw', 0),
                )
            except Exception as e:
                self.stderr.write(f"Erro ao salvar registro: {e}")

        self.stdout.write(self.style.SUCCESS("Importação concluída com sucesso!"))
