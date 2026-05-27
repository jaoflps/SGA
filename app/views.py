from django.shortcuts import render, redirect, get_object_or_404
from django.views import View
from django.contrib.auth import authenticate, login
from .models import *
from django.utils import timezone

# Novas importações necessárias para a inteligência analítica do Gestor
from django.db.models import Count, Sum, Avg
from django.db.models.functions import ExtractHour
import csv
from django.http import HttpResponse

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

# --- REESTRUTURAÇÃO COMPLETA: HOME GESTOR COM TODAS AS INTEGRAÇÕES SOLICITADAS ---
class HomeGestorView(View):
    def get(self, request):
        # --- 👥 GESTÃO DE USUÁRIOS ---
        todos_alunos = Usuario.objects.filter(tipo='ALUNO').order_by('username')
        todos_servidores = Usuario.objects.filter(tipo='SERVIDOR').order_by('username')
        comunicados = Comunicado.objects.all().order_by('-data_envio')
        
        # --- 📊 DASHBOARD GERAL ---
        qtd_alunos_alojados = Alocacao.objects.count()
        
        # Quartos vagos: Filtra quartos ativos que não possuem nenhuma alocação associada
        quartos_vagos = Quarto.objects.filter(status='ATIVO').annotate(num_moradores=Count('moradores')).filter(num_moradores=0).count()
        
        # Capacidade Total de Leitos em quartos disponíveis
        total_vagas = Quarto.objects.filter(status='ATIVO').aggregate(total=Sum('capacidade'))['total'] or 0
        taxa_ocupacao = (qtd_alunos_alojados / total_vagas * 100) if total_vagas > 0 else 0
        
        reclamacoes_abertas = Reclamacao.objects.filter(status='Pendente').count()
        
        # Problemas Recorrentes: Categorias de defeitos com mais ocorrências acumuladas
        problemas_recorrentes = Reclamacao.objects.values('categoria').annotate(total=Count('id')).order_by('-total')

        # --- 🧠 INTELIGÊNCIA DE GESTÃO ---
        # Bloco com maior volume cumulativo de reclamações (Bloco -> Quarto -> Alocação -> Aluno -> Reclamação)
        bloco_mais_problemas = Bloco.objects.annotate(total_def=Count('quarto__moradores__aluno__reclamacao')).order_by('-total_def').first()
        
        # Quarto com o maior histórico de reclamações (Quarto -> Alocação -> Aluno -> Reclamação)
        quarto_mais_reclamado = Quarto.objects.annotate(total_rec=Count('moradores__aluno__reclamacao')).order_by('-total_rec').first()
        
        # Horário estatístico com maior pico de registros de comunicados/ocorrências
        horario_analise = Comunicado.objects.annotate(hora=ExtractHour('data_envio')).values('hora').annotate(total=Count('id')).order_by('-total').first()
        horario_pico = f"{horario_analise['hora']}:00h" if horario_analise else "Sem registros"
        
        tipos_defeito_comuns = problemas_recorrentes.first()
        defeito_mais_comum = tipos_defeito_comuns['categoria'] if tipos_defeito_comuns else "N/A"
        
        # Ranking de manutenção: Servidores ordenados por quantidade de reparos resolvidos com sucesso
        ranking_manutencao = Usuario.objects.filter(tipo='SERVIDOR').annotate(resolvidos=Count('atendimentos', filter=models.Q(atendimentos__status='Resolvido'))).order_by('-resolvidos')

        # --- 💰 CUSTOS ---
        gastos_manutencao = Reclamacao.objects.aggregate(total=Sum('custo_reparo'))['total'] or 0
        
        # Consolidação de custos fixos adicionados à base de dados
        ultimo_custo = CustoFixoMensal.objects.order_by('-mes_referencia').first()
        consumo_agua = ultimo_custo.consumo_agua if ultimo_custo else 0
        consumo_luz = ultimo_custo.consumo_luz if ultimo_custo else 0
        
        total_despesas_atuais = gastos_manutencao + consumo_agua + consumo_luz
        previsao_despesas = total_despesas_atuais * 1.10 # Acréscimo estatístico de 10% para provisionamento preventivo

        # --- 🚨 DISCIPLINA ---
        advertencias = AdvertenciaDisciplinar.objects.all().order_by('-data_emissao')
        ocorrencias_comportamento = Comunicado.objects.filter(tipo='COMPORTAMENTO').order_by('-data_envio')
        
        # Identificação de reincidência: Alunos com mais de 1 advertência formalizada
        alunos_reincidentes = Usuario.objects.filter(tipo='ALUNO').annotate(num_adv=Count('advertencias')).filter(num_adv__gt=1).order_by('-num_adv')

        # --- 🏠 GESTÃO DE QUARTOS (CONTEÚDO DE APOIO PARA MODAIS DE CADASTRO) ---
        todos_quartos = Quarto.objects.all().order_by('bloco__nome', 'numero')
        todos_blocos = Bloco.objects.all()

        context = {
            'alunos': todos_alunos,
            'servidores': todos_servidores,
            'comunicados': comunicados,
            'qtd_alunos_alojados': qtd_alunos_alojados,
            'quartos_vagos': quartos_vagos,
            'taxa_ocupacao': round(taxa_ocupacao, 1),
            'reclamacoes_abertas': reclamacoes_abertas,
            'problemas_recorrentes': problemas_recorrentes,
            'bloco_mais_problemas': bloco_mais_problemas,
            'quarto_mais_reclamado': quarto_mais_reclamado,
            'horario_pico': horario_pico,
            'defeito_mais_comum': defeito_mais_comum,
            'ranking_manutencao': ranking_manutencao,
            'gastos_manutencao': gastos_manutencao,
            'consumo_agua': consumo_agua,
            'consumo_luz': consumo_luz,
            'previsao_despesas': round(previsao_despesas, 2),
            'advertencias': advertencias,
            'ocorrencias_comportamento': ocorrencias_comportamento,
            'alunos_reincidentes': alunos_reincidentes,
            'quartos': todos_quartos,
            'blocos': todos_blocos,
        }
        return render(request, 'home_gestor.html', context)

# --- Funções de Ação do Aluno ---

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

# --- Funções de Ação do Servidor ---

class HomeServidorView(View):
    def get(self, request):
        chamados = Reclamacao.objects.all().order_by('-urgente', '-data_criacao')
        context = {
            'chamados': chamados,
            'quartos_lista': Quarto.objects.all(),
            'alunos_lista': Usuario.objects.filter(tipo='ALUNO'),
        }
        return render(request, 'home_servidor.html', context)

def iniciar_reparo(request, pk):
    chamado = get_object_or_404(Reclamacao, pk=pk)
    chamado.status = 'Em Andamento'
    chamado.servidor_atendente = request.user # Associa o reparo ao servidor logado para o Ranking
    chamado.data_inicio_reparo = timezone.now()
    chamado.save()
    return redirect('home_servidor')

def concluir_reparo(request, pk):
    if request.method == 'POST':
        chamado = get_object_or_404(Reclamacao, pk=pk)
        chamado.status = 'Resolvido'
        chamado.data_fim_reparo = timezone.now()
        chamado.foto_depois = request.FILES.get('foto_depois')
        
        # Coleta custo informado pelo servidor no momento do encerramento
        custo = request.POST.get('custo_reparo')
        if custo:
            chamado.custo_reparo = custo
            
        chamado.save()
    return redirect('home_servidor')

def registrar_movimentacao(request):
    if request.method == 'POST':
        tipo = request.POST.get('tipo')
        aluno_id = request.POST.get('aluno')
        RegistroAcesso.objects.create(
            tipo=tipo,
            aluno_id=aluno_id if aluno_id else None,
            visitor_nome=request.POST.get('visitante_nome'),
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

# --- NOVAS FUNÇÕES DE AÇÃO OPERACIONAIS PARA O GESTOR ---

def gestor_aprovar_servidor(request, pk):
    servidor = get_object_or_404(Usuario, pk=pk, tipo='SERVIDOR')
    servidor.aprovado_gestor = True
    servidor.save()
    return redirect('home_gestor')

def gestor_mudar_status_usuario(request, pk):
    usuario = get_object_or_404(Usuario, pk=pk)
    # Inverte o status de bloqueio do usuário selecionado
    usuario.bloqueado = not usuario.bloqueado
    usuario.is_active = not usuario.bloqueado
    usuario.save()
    return redirect('home_gestor')

def gestor_status_quarto(request, pk):
    quarto = get_object_or_404(Quarto, pk=pk)
    # Alterna o status do quarto entre ATIVO e REFORMA
    if quarto.status == 'ATIVO':
        quarto.status = 'REFORMA'
    else:
        quarto.status = 'ATIVO'
    quarto.save()
    return redirect('home_gestor')

def gestor_emitir_advertencia(request):
    if request.method == 'POST':
        AdvertenciaDisciplinar.objects.create(
            aluno_id=request.POST.get('aluno'),
            motivo=request.POST.get('motivo'),
            gravidade=request.POST.get('gravidade')
        )
    return redirect('home_gestor')

def gestor_lancar_custos(request):
    if request.method == 'POST':
        CustoFixoMensal.objects.create(
            mes_referencia=request.POST.get('mes_referencia'),
            consumo_agua=request.POST.get('consumo_agua'),
            consumo_luz=request.POST.get('consumo_luz')
        )
    return redirect('home_gestor')

# --- OPERAÇÕES DE EXPORTAÇÃO DE RELATÓRIOS (EXCEL/CSV AUTOMÁTICO) ---

def gestor_exportar_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="historico_reparos.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Titulo', 'Categoria', 'Status', 'Custo (R$)', 'Data Criacao'])
    
    for relato in Reclamacao.objects.all().order_by('-data_criacao'):
        writer.writerow([relato.titulo, relato.get_categoria_display(), relato.status, relato.custo_reparo, relato.data_criacao])
        
    return response