from django.db import models


class Usina(models.Model):
    nome = models.CharField(max_length=255)
    estado = models.CharField(max_length=2)
    fonte = models.CharField(max_length=100)
    potencia_kw = models.FloatField()

    def __str__(self):
        return self.nome
