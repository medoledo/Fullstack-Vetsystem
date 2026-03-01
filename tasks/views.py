from django.shortcuts import render, redirect, get_object_or_404
from vetlogin.decorators import doctor_or_admin_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from .models import Task
from datetime import datetime, date


@doctor_or_admin_required
def tasks_dashboard(request):
    active_tasks = Task.objects.filter(is_done=False).order_by('deadline', '-date_created')

    # --- Date filter for completed tasks ---
    date_from_str = request.GET.get('date_from', '')
    date_to_str   = request.GET.get('date_to', '')

    completed_qs = Task.objects.filter(is_done=True).order_by('-date_created')

    if date_from_str:
        try:
            df = datetime.strptime(date_from_str, '%Y-%m-%d').date()
            completed_qs = completed_qs.filter(date_created__date__gte=df)
        except ValueError:
            pass

    if date_to_str:
        try:
            dt = datetime.strptime(date_to_str, '%Y-%m-%d').date()
            completed_qs = completed_qs.filter(date_created__date__lte=dt)
        except ValueError:
            pass

    # --- Pagination for completed tasks (10 per page) ---
    paginator  = Paginator(completed_qs, 10)
    page_number = request.GET.get('page', 1)
    page_obj   = paginator.get_page(page_number)

    context = {
        'active_tasks':  active_tasks,
        'page_obj':      page_obj,
        'date_from':     date_from_str,
        'date_to':       date_to_str,
        'current_time':  timezone.now(),
    }
    return render(request, 'taskspage/tasks.html', context)


@doctor_or_admin_required
def add_task(request):
    if request.method == 'POST':
        title        = request.POST.get('title')
        description  = request.POST.get('description')
        deadline_str = request.POST.get('deadline')

        deadline = None
        if deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str.replace('T', ' '))
                if timezone.is_naive(deadline):
                    deadline = timezone.make_aware(deadline)
            except ValueError:
                pass

        try:
            Task.objects.create(
                title=title,
                description=description,
                created_by=request.user,
                deadline=deadline,
            )
            messages.success(request, f"Task '{title}' created successfully.")
        except Exception as e:
            messages.error(request, f"Error creating task: {str(e)}")

    return redirect('tasks_dashboard')


@doctor_or_admin_required
def edit_task(request, task_id):
    task = get_object_or_404(Task, id=task_id)

    # Guard: only the creator can edit, and only if not yet completed
    if task.created_by != request.user:
        messages.error(request, "You can only edit tasks that you created.")
        return redirect('tasks_dashboard')

    if task.is_done:
        messages.error(request, "Completed tasks cannot be edited.")
        return redirect('tasks_dashboard')

    if request.method == 'POST':
        title        = request.POST.get('title')
        description  = request.POST.get('description')
        deadline_str = request.POST.get('deadline')

        deadline = None
        if deadline_str:
            try:
                deadline = datetime.fromisoformat(deadline_str.replace('T', ' '))
                if timezone.is_naive(deadline):
                    deadline = timezone.make_aware(deadline)
            except ValueError:
                pass

        try:
            task.title       = title
            task.description = description
            task.deadline    = deadline
            task.save()
            messages.success(request, f"Task '{title}' updated successfully.")
        except Exception as e:
            messages.error(request, f"Error updating task: {str(e)}")

    return redirect('tasks_dashboard')


@doctor_or_admin_required
def delete_task(request, task_id):
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id)

        # Guard: only the creator can delete, and only if not yet completed
        if task.created_by != request.user:
            messages.error(request, "You can only delete tasks that you created.")
            return redirect('tasks_dashboard')

        if task.is_done:
            messages.error(request, "Completed tasks cannot be deleted.")
            return redirect('tasks_dashboard')

        title = task.title
        task.delete()
        messages.success(request, f"Task '{title}' deleted.")

    return redirect('tasks_dashboard')


@doctor_or_admin_required
def complete_task(request, task_id):
    """Mark a task as completed. One-way: cannot be undone via UI."""
    if request.method == 'POST':
        task = get_object_or_404(Task, id=task_id)

        if task.is_done:
            messages.warning(request, f"Task '{task.title}' is already completed.")
            return redirect('tasks_dashboard')

        task.is_done  = True
        task.done_by  = request.user
        task.save()
        messages.success(request, f"Task '{task.title}' marked as completed.")

    return redirect('tasks_dashboard')
