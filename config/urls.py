from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static

# Importamos todas as views do seu app
from app.views import *

urlpatterns = [
    # Admin do Django
    path('admin/', admin.site.urls),
    
    # Autenticação e Index
    path('', IndexView.as_view(), name='index'),
    path('login/', LoginView.as_view(), name='login'),
    
    # Dashboards (Paineis)
    path('aluno/', HomeAlunoView.as_view(), name='home_aluno'),
    path('servidor/', HomeServidorView.as_view(), name='home_servidor'),
    path('gestor/', HomeGestorView.as_view(), name='home_gestor'),
    
    # Perfil do Usuário
    path('perfil/', PerfilView.as_view(), name='perfil'),
    
    # Ações do Sistema (Funções POST)
    path('criar-chamado/', criar_chamado, name='criar_chamado'),
    path('solicitar-troca/', solicitar_troca, name='solicitar_troca'),
    path('enviar-comunicado/', enviar_comunicado, name='enviar_comunicado'),
    path('iniciar-reparo/<int:pk>/', iniciar_reparo, name='iniciar_reparo'),
    path('concluir-reparo/<int:pk>/', concluir_reparo, name='concluir_reparo'),
    path('registrar-movimentacao/', registrar_movimentacao, name='registrar_movimentacao'),
    path('realizar-vistoria/', realizar_vistoria, name='realizar_vistoria'),
]

# Configuração para exibir fotos (Mídia) durante o desenvolvimento
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)