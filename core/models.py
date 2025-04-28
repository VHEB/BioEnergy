from django.db import models

nom_empreendimento = models.CharField(
    "Empreendimento",
    max_length=255,
    blank=True,        # permite campo vazio
    default=""         # default para linhas antigas
)


class Usina(models.Model):
    dat_geracao                     = models.DateField(null=True, blank=True)
    nom_empreendimento              = models.CharField("Empreendimento", max_length=255)
    ide_nucleo_ceg                  = models.CharField("ID Núcleo CEG", max_length=50, blank=True)
    cod_ceg                         = models.CharField("Código CEG", max_length=50, blank=True)
    sigla_uf_principal              = models.CharField("UF", max_length=2, blank=True)
    sig_tipo_geracao                = models.CharField("Tipo de Geração", max_length=50, blank=True)
    dsc_fase_usina                  = models.CharField("Fase da Usina", max_length=50, blank=True)
    dsc_origem_combustivel          = models.CharField("Origem Combustível", max_length=100, blank=True)
    dsc_fonte_combustivel           = models.CharField("Fonte Combustível", max_length=100, blank=True)
    dsc_tipo_outorga                = models.CharField("Tipo Outorga", max_length=100, blank=True)
    nom_fonte_combustivel           = models.CharField("Nome Fonte Combustível", max_length=150, blank=True)
    dat_entrada_operacao            = models.DateField("Data Entrada Operação", null=True, blank=True)
    mda_pot_outorgada_kw            = models.FloatField("Potência Outorgada (kW)", default=0.0)
    mda_pot_fiscalizada_kw          = models.FloatField("Potência Fiscalizada (kW)", default=0.0)
    mda_garantia_fisica_kw          = models.FloatField("Garantia Física (kW)", default=0.0)
    idc_geracao_qualificada         = models.BooleanField("Geração Qualificada", default=False)
    num_coord_n_emp                 = models.FloatField("Latitude", null=True, blank=True)
    num_coord_e_emp                 = models.FloatField("Longitude", null=True, blank=True)
    dat_inicio_vigencia             = models.DateField("Início Vigência", null=True, blank=True)
    dat_fim_vigencia                = models.DateField("Fim Vigência", null=True, blank=True)
    dsc_propri_regime_participacao  = models.TextField("Regime Participação", blank=True)
    dsc_sub_bacia                   = models.TextField("Sub-bacia", blank=True)
    dsc_municipios                  = models.TextField("Municípios", blank=True)

    def __str__(self):
        return f"{self.nom_empreendimento} ({self.sigla_uf_principal})"

