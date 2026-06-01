from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    AdvertenciaDisciplinar,
    Alocacao,
    Bloco,
    Cidade,
    Comunicado,
    Curso,
    CustoFixoMensal,
    Quarto,
    Reclamacao,
    RegistroAcesso,
    SolicitacaoTroca,
    Usuario,
    VistoriaQuarto,
)

# --- 🛠️ IMPLEMENTAÇÃO DE INLINES (Exigência Disciplina PSOO) ---

class QuartoInline(admin.TabularInline):
    """Permite gerenciar os Quartos diretamente na tela de edição do Bloco"""
    model = Quarto
    extra = 1

class AlocacaoInline(admin.TabularInline):
    """Permite alocar alunos diretamente na tela de edição do Quarto"""
    model = Alocacao
    extra = 1


# --- 👥 1. Configuração do Usuário Customizado (CPF, Foto, Curso, Cidade, Integridade) ---
class UsuarioAdmin(UserAdmin):
    # Campos que aparecem ao editar um usuário existente (Atualizado com novos campos do Gestor)
    fieldsets = UserAdmin.fieldsets + (
        ('Informações do SGA', {
            'fields': ('cpf', 'tipo', 'foto', 'curso', 'cidade', 'data_nascimento', 'integridade', 'aprovado_gestor', 'bloqueado')
        }),
    )
    
    # Campos que aparecem ao criar um novo usuário no Admin (Atualizado com novos campos do Gestor)
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações do SGA', {
            'fields': ('cpf', 'tipo', 'email', 'foto', 'curso', 'cidade', 'data_nascimento', 'integridade', 'aprovado_gestor', 'bloqueado')
        }),
    )
    
    # Colunas que aparecem na lista de usuários
    list_display = ('username', 'cpf', 'tipo', 'curso', 'integridade', 'aprovado_gestor', 'bloqueado', 'is_staff')
    list_filter = ('tipo', 'curso', 'cidade', 'aprovado_gestor', 'bloqueado')
    search_fields = ('username', 'cpf', 'curso__nome')


# --- 🔧 2. Configuração das Reclamações (Chamados técnicos) ---
@admin.register(Reclamacao)
class ReclamacaoAdmin(admin.ModelAdmin):
    # Unificado e corrigido para exibir todas as colunas essenciais, incluindo Custos e Atendente
    list_display = ('titulo', 'aluno', 'categoria', 'status', 'urgente', 'custo_reparo', 'servidor_atendente', 'data_criacao')
    list_filter = ('status', 'categoria', 'urgente', 'data_criacao')
    search_fields = ('titulo', 'aluno__username', 'descricao')
    readonly_fields = ('data_inicio_reparo', 'data_fim_reparo') # Evita edição manual do tempo


# --- 🏠 3. Configuração de Alocações (Controle de quem está em qual quarto) ---
@admin.register(Alocacao)
class AlocacaoAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'quarto', 'data_alocacao')
    search_fields = ('aluno__username', 'quarto__numero')


# --- 🔄 4. Configuração das Solicitações de Troca de Quarto ---
@admin.register(SolicitacaoTroca)
class SolicitacaoTrocaAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'status', 'data_solicitacao')
    list_filter = ('status',)


# --- 📢 5. Configuração de Comunicados (Denúncias, Comportamento e Perda de Chave) ---
@admin.register(Comunicado)
class ComunicadoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'autor', 'quarto_relacionado', 'data_envio')
    list_filter = ('tipo', 'data_envio')


# --- 🏢 6. Customização de Estrutura Física com Inlines ---
@admin.register(Bloco)
class BlocoAdmin(admin.ModelAdmin):
    list_display = ('nome',)
    inlines = [QuartoInline] # Vincula Quartos ao Bloco na mesma tela (PSOO)

@admin.register(Quarto)
class QuartoAdmin(admin.ModelAdmin):
    list_display = ('numero', 'bloco', 'capacidade', 'status')
    list_filter = ('bloco', 'status')
    search_fields = ('numero', 'bloco__nome')
    inlines = [AlocacaoInline] # Vincula Alocações ao Quarto na mesma tela (PSOO)


# --- 🚨 7. Configurações dos Novos Modelos do Gestor (Custos e Disciplina) ---
@admin.register(CustoFixoMensal)
class CustoFixoMensalAdmin(admin.ModelAdmin):
    list_display = ('mes_referencia', 'consumo_agua', 'consumo_luz')
    list_filter = ('mes_referencia',)

@admin.register(AdvertenciaDisciplinar)
class AdvertenciaDisciplinarAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'gravidade', 'data_emissao')
    list_filter = ('gravidade', 'data_emissao')
    search_fields = ('aluno__username', 'motivo')


# --- 📦 8. Registros Adicionais das Tabelas Auxiliares ---
admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Cidade)
admin.site.register(Curso)
admin.site.register(RegistroAcesso)
admin.site.register(VistoriaQuarto)
