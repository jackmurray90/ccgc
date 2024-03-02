from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from datetime import datetime

from ccgc.forms import UploadFileForm
from ccgc.models import CsvFile
from ccgc.engine import calculate

class IndexView(View):
    def get(self, request):
        if request.user.is_authenticated:
            form = UploadFileForm()
            return render(request, "dashboard.html", {"form": form})
        else:
            return render(request, "landing_page.html")


class UploadFileView(View):
    def post(self, request):
        if request.user.is_authenticated:
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                if request.FILES['file'].size > 10 * 1024 * 1024:
                    messages.error(request, "Maximum file size is 10 MB.")
                else:
                    CsvFile.objects.create(
                        user=request.user,
                        file=request.FILES['file'],
                        filename=request.FILES['file'].name,
                        uploaded_at=datetime.now(),
                    )
            else:
                messages.error(request, "No CSV file was selected.")
        return redirect("index")

class DeleteFileView(View):
    def post(self, request, id):
        if request.user.is_authenticated:
            CsvFile.objects.filter(user=request.user, id=id).delete()
        return redirect("index")

class CalculateView(View):
    def get(self, request):
        if not request.user.is_authenticated:
            return redirect("index")
        result = calculate(request.user.csv_files.all())
        return render(request, "calculate.html", {"result": result})
