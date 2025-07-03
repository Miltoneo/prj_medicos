from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from .forms import EmailAuthenticationForm, CustomUserCreationForm

# ---------------------------------------------
def login_view(request):
    if request.method == 'POST':
        form = EmailAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = authenticate(
                request,
                username=form.cleaned_data['username'],
                password=form.cleaned_data['password']
            )
            if user is not None:
                login(request, user)
                return redirect('medicos:index')
    else:
        form = EmailAuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})

# ---------------------------------------------
def logout_view(request):
    logout(request)
    return redirect('medicos:login')

# ---------------------------------------------
def register_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('medicos:login')
    else:
        form = CustomUserCreationForm()
    return render(request, 'auth/register.html', {'form': form})