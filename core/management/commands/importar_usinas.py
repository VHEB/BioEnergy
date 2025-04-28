import os
import pandas as pd
from django.conf import settings
from django.core.management.base import BaseCommand
from core.models import Usina

CSV_FILENAME = "siga-empreendimentos-geracao.csv"

class Command(BaseCommand):
    help = "Importa CSV da ANEEL para o modelo Usina"

    def handle(self, *args, **options):
        # caminho absoluto para o CSV na raiz do projeto
        csv_path = os.path.join(settings.BASE_DIR, CSV_FILENAME)
        if not os.path.exists(csv_path):
            self.stderr.write(f"Arquivo não encontrado: {csv_path}")
            return

        # lê o CSV
        df = pd.read_csv(
            csv_path,
            sep=';',
            encoding='latin1',
            dayfirst=True,  # datas no formato DD/MM/YYYY
            parse_dates=[
                'DatGeracaoConjuntoDados',
                'DatEntradaOperacao',
                'DatInicioVigencia',
                'DatFimVigencia'
            ]
        )

        self.stdout.write(f"Lendo {len(df)} linhas de {CSV_FILENAME}…")

        # opcional: limpa tabela antes de importar
        Usina.objects.all().delete()

        # prepara lista de objetos
        lote = []
        for _, row in df.iterrows():
            # converte "Sim"/"Não" em booleano
            qualificada = True if str(row.get('IdcGeracaoQualificada','')).strip().lower() == 'sim' else False

            # tenta converter coords
            def to_float(val):
                try:
                    return float(str(val).replace(',', '.'))
                except:
                    return None

            usina = Usina(
                dat_geracao                    = row.get('DatGeracaoConjuntoDados'),
                nom_empreendimento             = row.get('NomEmpreendimento','').strip(),
                ide_nucleo_ceg                 = row.get('IdeNucleoCEG','').strip(),
                cod_ceg                        = row.get('CodCEG','').strip(),
                sigla_uf_principal             = row.get('SigUFPrincipal','').strip(),
                sig_tipo_geracao               = row.get('SigTipoGeracao','').strip(),
                dsc_fase_usina                 = row.get('DscFaseUsina','').strip(),
                dsc_origem_combustivel         = row.get('DscOrigemCombustivel','').strip(),
                dsc_fonte_combustivel          = row.get('DscFonteCombustivel','').strip(),
                dsc_tipo_outorga               = row.get('DscTipoOutorga','').strip(),
                nom_fonte_combustivel          = row.get('NomFonteCombustivel','').strip(),
                dat_entrada_operacao           = row.get('DatEntradaOperacao'),
                mda_pot_outorgada_kw           = row.get('MdaPotenciaOutorgadaKw') or 0.0,
                mda_pot_fiscalizada_kw         = row.get('MdaPotenciaFiscalizadaKw') or 0.0,
                mda_garantia_fisica_kw         = row.get('MdaGarantiaFisicaKw') or 0.0,
                idc_geracao_qualificada        = qualificada,
                num_coord_n_emp                = to_float(row.get('NumCoordNEmpreendimento')),
                num_coord_e_emp                = to_float(row.get('NumCoordEEmpreendimento')),
                dat_inicio_vigencia            = row.get('DatInicioVigencia'),
                dat_fim_vigencia               = row.get('DatFimVigencia'),
                dsc_propri_regime_participacao = row.get('DscPropriRegimePariticipacao','').strip(),
                dsc_sub_bacia                  = row.get('DscSubBacia','').strip(),
                dsc_municipios                 = row.get('DscMuninicpios','').strip(),
            )
            lote.append(usina)

        # insere em batch
        Usina.objects.bulk_create(lote, batch_size=1000)
        self.stdout.write(self.style.SUCCESS(f"{len(lote)} usinas importadas com sucesso!"))
