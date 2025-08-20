from django.shortcuts import render, redirect, get_object_or_404
from core.decorators import admin_required
from django.contrib.auth.decorators import login_required
from ..models import RoomLayout
from ..forms import RoomLayoutForm

@login_required
@admin_required
def room_layout_list(request):
    query = request.GET.get("q", "")
    room_layouts = RoomLayout.objects.all()

    if query:
        room_layouts = room_layouts.filter(
            Q(name__icontains=query) |
            Q(building_type__icontains=query)
        )

    return render(request, "admin/room_layout/room_list.html", {"room_layouts": room_layouts, "query": query})


@login_required
@admin_required
def room_layout_create(request):
    if request.method == "POST":
        form = RoomLayoutForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("room_layout_list")
    else:
        form = RoomLayoutForm()
    return render(request, "admin/room_layout/room_form.html", {"form": form, "title": "Создание планировки"})


@login_required
@admin_required
def room_layout_edit(request, pk):
    layout = get_object_or_404(RoomLayout, pk=pk)
    if request.method == "POST":
        form = RoomLayoutForm(request.POST, instance=layout)
        if form.is_valid():
            form.save()
            return redirect("room_layout_list")
    else:
        form = RoomLayoutForm(instance=layout)
    return render(request, "admin/room_layout/room_form.html", {"form": form, "title": "Редактирование планировки"})