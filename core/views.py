from django.shortcuts import render
from .models import Usina

def index(request):
    usinas = Usina.objects.all()[:20]  # Limita para evitar carregar tudo de uma vez
    return render(request, 'core/index.html', {'usinas': usinas})
