from django.shortcuts import render, redirect, get_object_or_404
from core.decorators import admin_required
from django.contrib.auth.decorators import login_required
from ..models import Relative
from ..forms import RelativeForm


@login_required
@admin_required
def relatives_list(request):
    relatives = Relative.objects.select_related('user').all()
    return render(request, 'admin/relatives/relatives_list.html', {'relatives': relatives})


@login_required
@admin_required
def relative_create(request):
    if request.method == "POST":
        form = RelativeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('relatives_list')
    else:
        form = RelativeForm()
    return render(request, 'admin/relatives/relative_form.html', {'form': form, 'title': 'Добавить родственника'})


@login_required
@admin_required
def relative_edit(request, relative_id):
    relative = get_object_or_404(Relative, id=relative_id)
    if request.method == "POST":
        form = RelativeForm(request.POST, instance=relative)
        if form.is_valid():
            form.save()
            return redirect('relatives_list')
    else:
        form = RelativeForm(instance=relative)
    return render(request, 'admin/relatives/relative_form.html', {'form': form, 'title': 'Редактировать родственника'})
