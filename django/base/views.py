from django.shortcuts import render

# Create your views here.
from django.template import loader,Context
from django.http import HttpResponse

def index(request):
    #posts = BlogPost.objects.all()
    t = loader.get_template('base.html')
    #c = Context({'posts': posts})
    #return HttpResponse(t.render(c))
    return HttpResponse(t.render())
