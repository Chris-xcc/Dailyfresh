from django.shortcuts import render
from django.views.generic import View


# http://127.0.0.1:8000
class IndexView(View):
    def get(self, request):
        return render(request, 'index.html')
