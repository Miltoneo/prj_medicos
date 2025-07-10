from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from medicos.models.base import Empresa, Socio, Pessoa
from medicos.forms import SocioCPFForm, SocioPessoaForm, SocioForm
from django.contrib import messages

@login_required
def socio_create(request, empresa_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    # Corrigido: obtém step do GET se não houver POST
    step = request.POST.get('step') or request.GET.get('step') or 'cpf'
    context = {'empresa': empresa}

    if step == 'cpf':
        cpf_form = SocioCPFForm(request.POST or None)
        if request.method == 'POST' and cpf_form.is_valid():
            cpf = cpf_form.cleaned_data['cpf']
            pessoa = Pessoa.objects.filter(cpf=cpf).first()
            if pessoa:
                request.session['socio_cpf'] = cpf
                return redirect(f"{request.path}?step=socio")
            else:
                request.session['socio_cpf'] = cpf
                return redirect(f"{request.path}?step=pessoa")
        context['cpf_form'] = cpf_form
        context['step'] = 'cpf'
        return render(request, 'empresa/socio_form_cpf.html', context)

    elif step == 'pessoa':
        initial = {'cpf': request.session.get('socio_cpf', '')}
        pessoa_form = SocioPessoaForm(request.POST or None, initial=initial, empresa=empresa)
        if request.method == 'POST' and pessoa_form.is_valid():
            pessoa = pessoa_form.save()
            request.session['socio_pessoa_id'] = pessoa.id
            return redirect(f"{request.path}?step=socio")
        context['pessoa_form'] = pessoa_form
        context['step'] = 'pessoa'
        return render(request, 'empresa/socio_form_pessoa.html', context)

    elif step == 'socio':
        cpf = request.session.get('socio_cpf')
        pessoa_id = request.session.get('socio_pessoa_id')
        pessoa = Pessoa.objects.filter(id=pessoa_id).first() if pessoa_id else Pessoa.objects.filter(cpf=cpf).first()
        if not pessoa:
            messages.error(request, 'Pessoa não encontrada. Reinicie o cadastro.')
            return redirect('medicos:lista_socios_empresa', empresa_id=empresa.id)
        socio_form = SocioForm(request.POST or None)
        if request.method == 'POST' and socio_form.is_valid():
            socio = socio_form.save(commit=False)
            socio.empresa = empresa
            socio.conta = empresa.conta
            socio.pessoa = pessoa
            socio.save()
            request.session.pop('socio_cpf', None)
            request.session.pop('socio_pessoa_id', None)
            messages.success(request, 'Sócio cadastrado com sucesso!')
            return redirect('medicos:lista_socios_empresa', empresa_id=empresa.id)
        context['socio_form'] = socio_form
        context['pessoa'] = pessoa
        context['step'] = 'socio'
        return render(request, 'empresa/socio_form_socio.html', context)

@login_required
def socio_edit(request, empresa_id, socio_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    socio = get_object_or_404(Socio, id=socio_id, empresa=empresa)
    if request.method == 'POST':
        form = SocioForm(request.POST, instance=socio)
        if form.is_valid():
            form.save()
            messages.success(request, 'Sócio atualizado com sucesso!')
            return redirect('medicos:lista_socios_empresa', empresa_id=empresa.id)
    else:
        form = SocioForm(instance=socio)
    context = {
        'empresa': empresa,
        'socio_form': form,
        'pessoa': socio.pessoa,
        'step': 'socio',
        'edit_mode': True
    }
    return render(request, 'empresa/socio_form_socio.html', context)

@login_required
def socio_unlink(request, empresa_id, socio_id):
    empresa = get_object_or_404(Empresa, id=empresa_id)
    socio = get_object_or_404(Socio, id=socio_id, empresa=empresa)
    if request.method == 'POST':
        socio.delete()
        messages.success(request, 'Sócio desvinculado da empresa com sucesso!')
        return redirect('medicos:lista_socios_empresa', empresa_id=empresa.id)
    context = {
        'empresa': empresa,
        'socio': socio
    }
    return render(request, 'empresa/socio_confirm_unlink.html', context)
