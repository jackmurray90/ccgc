from django.shortcuts import render
from django.views import View


class IndexView(View):
    def get(self, request):
        if request.user.is_authenticated:
            return render(request, "dashboard.html")
        else:
            return render(request, "landing_page.html")
