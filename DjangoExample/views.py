from django.http import HttpResponse
from django.shortcuts import render
from DjangoExample.settings import BASE_DIR
import datetime




"""def Bienvenido(request):
    hora_actual = datetime.datetime.now()

    cargar = 'Esta es mi primera vista! cargada a la fecha %s' % hora_actual
    return HttpResponse(cargar)"""

"""def Index(request):
    #category_list = Category.objects.all()
    #cajita = {"a": "Presiona aqui"}
    #context = {'object_list': category_list}
    base = {'directorio':BASE_DIR}
    return render(request, "index.html", base)"""

"""def casa(request, no): #1 Añadiendo parametros en las urls.

    caja_texto = 'Aprendiendo a usar parametros en las urls añadiendo %s' %no 
    return HttpResponse(caja_texto)"""


def Index(request):
    return render(request, "index.html")

def Servicios(request):
    return render(request, "services.html")

def Contacto(request):
    return render(request, "contact.html")

def Acercade(request):
    return render(request, "about.html")

