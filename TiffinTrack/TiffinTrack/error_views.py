from django.shortcuts import render


def bad_request(request, exception):
    return render(request, "errors/400.html", status=400)


def permission_denied(request, exception):
    return render(request, "errors/403.html", status=403)


def page_not_found(request, exception):
    return render(request, "errors/404.html", status=404)


def server_error(request):
    return render(request, "errors/500.html", status=500)
