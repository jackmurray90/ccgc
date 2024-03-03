from django.shortcuts import render, redirect
from django.views import View
from django.contrib import messages
from django.utils import timezone

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


class PasswordChangeRedirectView(View):
    def get(self, request):
        messages.info(request, "Your password was successfully changed.")
        return redirect("index")


class UploadFileView(View):
    def post(self, request):
        if request.user.is_authenticated:
            form = UploadFileForm(request.POST, request.FILES)
            if form.is_valid():
                for file in form.cleaned_data["files"]:
                    if file.size > 10 * 1024 * 1024:
                        messages.error(request, "Maximum file size is 10 MB.")
                        break
                else:
                    for file in form.cleaned_data["files"]:
                        CsvFile.objects.create(
                            user=request.user,
                            file=file,
                            filename=file.name,
                            uploaded_at=timezone.now(),
                        )
                    count = len(form.cleaned_data['files'])
                    messages.info(request, "1 file was uploaded" if count == 1 else f"{count} files were uploaded.")
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
