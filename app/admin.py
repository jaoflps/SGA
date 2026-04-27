from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
# 1. Configuração do Usuário Customizado (CPF, Foto, Curso, Cidade, Integridade)
class UsuarioAdmin(UserAdmin):
    # Campos que aparecem ao editar um usuário existente
    fieldsets = UserAdmin.fieldsets + (
        ('Informações do SGA', {
            'fields': ('cpf', 'tipo', 'foto', 'curso', 'cidade', 'data_nascimento', 'integridade')
        }),
    )
    
    # Campos que aparecem ao criar um novo usuário no Admin
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Informações do SGA', {
            'fields': ('cpf', 'tipo', 'email', 'foto', 'curso', 'cidade', 'data_nascimento', 'integridade')
        }),
    )
    
    # Colunas que aparecem na lista de usuários
    list_display = ('username', 'cpf', 'tipo', 'curso', 'integridade', 'is_staff')
    list_filter = ('tipo', 'curso', 'cidade')
    search_fields = ('username', 'cpf', 'curso__nome')

# 2. Configuração das Reclamações (Chamados técnicos)
@admin.register(Reclamacao)
class ReclamacaoAdmin(admin.ModelAdmin):
    list_display = ('titulo', 'aluno', 'categoria', 'status', 'urgente', 'data_criacao')
    list_filter = ('status', 'categoria', 'urgente')
    search_fields = ('titulo', 'aluno__username', 'descricao')
    list_display = ('titulo', 'status', 'urgente', 'data_inicio_reparo', 'data_fim_reparo')
    readonly_fields = ('data_inicio_reparo', 'data_fim_reparo') # Evita edição manual do tempo


# 3. Configuração de Alocações (Controle de quem está em qual quarto)
@admin.register(Alocacao)
class AlocacaoAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'quarto')
    search_fields = ('aluno__username', 'quarto__numero')

# 4. Configuração das Solicitações de Troca de Quarto
@admin.register(SolicitacaoTroca)
class SolicitacaoTrocaAdmin(admin.ModelAdmin):
    list_display = ('aluno', 'status', 'data_solicitacao')
    list_filter = ('status',)

# 5. Configuração de Comunicados (Denúncias, Comportamento e Perda de Chave)
@admin.register(Comunicado)
class ComunicadoAdmin(admin.ModelAdmin):
    list_display = ('tipo', 'autor', 'data_envio')
    list_filter = ('tipo', 'data_envio')


# 6. Registros Adicionais (Tabelas auxiliares e Moradia)
admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Bloco)
admin.site.register(Quarto)
admin.site.register(Cidade)
admin.site.register(Curso)
admin.site.register(RegistroAcesso)
admin.site.register(VistoriaQuarto)
