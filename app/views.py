from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login
from .models import *
from django.utils import timezone

class IndexView(View):
    def get(self, request):
        return render(request, 'index.html')

class LoginView(View):
    def get(self, request):
        return render(request, 'login.html')

    def post(self, request):
        cpf_digitado = request.POST.get('cpf')
        senha_digitada = request.POST.get('password')
        
        user = authenticate(request, cpf=cpf_digitado, password=senha_digitada)
        
        if user is not None:
            login(request, user)
            if user.tipo == 'ALUNO':
                return redirect('home_aluno')
            elif user.tipo == 'SERVIDOR':
                return redirect('home_servidor')
            elif user.tipo == 'GESTOR':
                return redirect('home_gestor')
            elif user.tipo == 'ADM':
                return redirect('/admin/')
        else:
            return render(request, 'login.html', {'erro': 'CPF ou Senha incorretos'})

class HomeAlunoView(View):
    def get(self, request):
        # Busca a moradia e os colegas
        alocacao = Alocacao.objects.filter(aluno=request.user).first()
        colegas = []
        quarto = None

        if alocacao:
            quarto = alocacao.quarto
            colegas = Alocacao.objects.filter(quarto=quarto).exclude(aluno=request.user)

        # Histórico de reclamações
        meus_relatos = Reclamacao.objects.filter(aluno=request.user).order_by('-data_criacao')

        context = {
            'quarto': quarto,
            'colegas': colegas,
            'relatos': meus_relatos
        }
        return render(request, 'home_aluno.html', context)

class PerfilView(View):
    def get(self, request):
        # Busca moradia para exibir no perfil
        moradia = Alocacao.objects.filter(aluno=request.user).first()
        
        context = {
            'aluno': request.user,
            'quarto': moradia.quarto if moradia else "Não alocado",
        }
        return render(request, 'perfil.html', context)

class HomeServidorView(View):
    def get(self, request):
        # O servidor vê todos os chamados pendentes
        chamados = Reclamacao.objects.all().order_by('-urgente', '-data_criacao')
        return render(request, 'home_servidor.html', {'chamados': chamados})

class HomeGestorView(View):
    def get(self, request):
        todos_alunos = Usuario.objects.filter(tipo='ALUNO')
        todos_servidores = Usuario.objects.filter(tipo='SERVIDOR')
        comunicados = Comunicado.objects.all().order_by('-data_envio')
        
        context = {
            'alunos': todos_alunos,
            'servidores': todos_servidores,
            'comunicados': comunicados,
        }
        return render(request, 'home_gestor.html', context)

# --- Funções de Ação ---

def criar_chamado(request):
    if request.method == 'POST':
        Reclamacao.objects.create(
            aluno=request.user,
            titulo=request.POST.get('titulo'),
            categoria=request.POST.get('categoria'),
            descricao=request.POST.get('descricao'),
            urgente=request.POST.get('urgente') == 'on',
            foto=request.FILES.get('foto'),
            video=request.FILES.get('video')
        )
    return redirect('home_aluno')

def solicitar_troca(request):
    if request.method == 'POST':
        SolicitacaoTroca.objects.create(
            aluno=request.user,
            motivo=request.POST.get('motivo')
        )
    return redirect('home_aluno')

def enviar_comunicado(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        anonimo = request.POST.get('anonimo') == 'on'
        
        Comunicado.objects.create(
            tipo=tipo,
            descricao=request.POST.get('descricao'),
            autor=None if (tipo == 'DENUNCIA' or anonimo) else request.user
        )
    return redirect('home_aluno')
# app/views.py

class HomeServidorView(View):
    def get(self, request):
        # Ver chamados por prioridade (Urgentes primeiro)
        chamados = Reclamacao.objects.all().order_by('-urgente', '-data_criacao')
        
        # Adicionamos a busca pelos alunos para o modal de portaria funcionar
        context = {
            'chamados': chamados,
            'quartos_lista': Quarto.objects.all(),
            'alunos_lista': Usuario.objects.filter(tipo='ALUNO'), # Busca apenas quem é aluno
        }
        
        return render(request, 'home_servidor.html', context)
def iniciar_reparo(request, pk):
    chamado = get_object_or_404(Reclamacao, pk=pk)
    chamado.status = 'Em Andamento'
    chamado.data_inicio_reparo = timezone.now()
    chamado.save()
    return redirect('home_servidor')

def concluir_reparo(request, pk):
    if request.method == 'POST':
        chamado = get_object_or_404(Reclamacao, pk=pk)
        chamado.status = 'Resolvido'
        chamado.data_fim_reparo = timezone.now()
        chamado.foto_depois = request.FILES.get('foto_depois')
        chamado.save()
    return redirect('home_servidor')

def registrar_movimentacao(request):
    if request.method == 'POST':
        # Lógica para salvar entrada/saída de aluno ou visitante
        tipo = request.POST.get('tipo')
        aluno_id = request.POST.get('aluno')
        RegistroAcesso.objects.create(
            tipo=tipo,
            aluno_id=aluno_id if aluno_id else None,
            visitante_nome=request.POST.get('visitante_nome'),
            visitante_documento=request.POST.get('visitante_documento')
        )
    return redirect('home_servidor')

def realizar_vistoria(request):
    if request.method == 'POST':
        VistoriaQuarto.objects.create(
            quarto_id=request.POST.get('quarto'),
            servidor=request.user,
            cama_organizada='cama' in request.POST,
            danos='danos' in request.POST,
            limpeza='limpeza' in request.POST,
            itens_proibidos='itens' in request.POST,
            observacoes=request.POST.get('observacoes'),
            foto_vistoria=request.FILES.get('foto')
        )
    return redirect('home_servidor')