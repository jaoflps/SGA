from django.contrib.auth.models import AbstractUser
from django.db import models
from datetime import date

# --- Modelos de Apoio ---

class Cidade(models.Model):
    nome = models.CharField(max_length=100)
    estado = models.CharField(max_length=2, help_text="Sigla (ex: SP)")

    def __str__(self):
        return f"{self.nome} - {self.estado}"

class Curso(models.Model):
    nome = models.CharField(max_length=100)
    sigla = models.CharField(max_length=10, blank=True)

    def __str__(self):
        return self.nome

class Bloco(models.Model):
    nome = models.CharField(max_length=50)
    regras = models.TextField(default="Respeitar o horário de silêncio após as 22h.")

    def __str__(self):
        return self.nome

class Quarto(models.Model):
    STATUS_CHOICES = [
        ('ATIVO', 'Ativo / Disponível'),
        ('REFORMA', 'Interditado para Reforma'),
    ]
    
    numero = models.CharField(max_length=10)
    bloco = models.ForeignKey(Bloco, on_delete=models.CASCADE)
    capacidade = models.IntegerField(default=4)
    
    # Adicionado para a funcionalidade: "Fechar quarto para reforma"
    status = models.CharField(max_length=15, choices=STATUS_CHOICES, default='ATIVO')

    def __str__(self):
        return f"{self.bloco.nome} - Quarto {self.numero}"

# --- Modelo de Usuário Customizado ---

class Usuario(AbstractUser):
    TIPOS = [
        ('ALUNO', 'Aluno'),
        ('SERVIDOR', 'Servidor'),
        ('GESTOR', 'Gestor'),
        ('ADM', 'Administrador'),
    ]
    
    cpf = models.CharField(max_length=11, unique=True)
    tipo = models.CharField(max_length=10, choices=TIPOS, default='ALUNO')
    foto = models.ImageField(upload_to='perfis/', null=True, blank=True, default='perfis/default.png')
    curso = models.ForeignKey(Curso, on_delete=models.SET_NULL, null=True, blank=True)
    cidade = models.ForeignKey(Cidade, on_delete=models.SET_NULL, null=True, blank=True)
    data_nascimento = models.DateField(null=True, blank=True)
    integridade = models.IntegerField(default=100) # 0 a 100%
    
    # Adicionado para as funcionalidades: "Aprovar servidores" e "Bloquear usuários"
    aprovado_gestor = models.BooleanField(default=False, help_text="Define se o servidor foi validado pelo gestor.")
    bloqueado = models.BooleanField(default=False, help_text="Indica se o usuário está suspenso do alojamento.")

    @property
    def idade(self):
        if self.data_nascimento:
            today = date.today()
            return today.year - self.data_nascimento.year - ((today.month, today.day) < (self.data_nascimento.month, self.data_nascimento.day))
        return "N/A"

    USERNAME_FIELD = 'cpf'
    REQUIRED_FIELDS = ['username', 'email']

    def __str__(self):
        return f"{self.username} - {self.get_tipo_display()}"

# --- Modelos de Sistema (Chamados e Alocações) ---

class Alocacao(models.Model):
    aluno = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='moradia')
    quarto = models.ForeignKey(Quarto, on_delete=models.CASCADE, related_name='moradores')
    
    # Adicionado para compor o histórico anual de alocações do Gestor
    data_alocacao = models.DateTimeField(auto_now_add=True, null=True, blank=True)

    def __str__(self):
        return f"{self.aluno.username} no {self.quarto}"

class Reclamacao(models.Model):
    CATEGORIAS = [
        ('ELETRICA', 'Elétrica'),
        ('HIDRAULICA', 'Hidráulica'),
        ('BARULHO', 'Barulho'),
        ('SEGURANCA', 'Segurança'),
    ]
    
    aluno = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    titulo = models.CharField(max_length=100)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS)
    descricao = models.TextField()
    urgente = models.BooleanField(default=False)
    
    foto = models.ImageField(upload_to='reclamacoes/fotos/', null=True, blank=True)
    video = models.FileField(upload_to='reclamacoes/videos/', null=True, blank=True)
    
    status = models.CharField(max_length=20, default='Pendente')
    data_criacao = models.DateTimeField(auto_now_add=True)

    oto_antes = models.ImageField(upload_to='reparos/antes/', null=True, blank=True) # Já era o 'foto' antigo
    foto_depois = models.ImageField(upload_to='reparos/depois/', null=True, blank=True)
    data_inicio_reparo = models.DateTimeField(null=True, blank=True)
    data_fim_reparo = models.DateTimeField(null=True, blank=True)
    
    # Adicionados para funcionalidades: "Custos com manutenção" e "Ranking de manutenção"
    custo_reparo = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    servidor_atendente = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='atendimentos')

    @property
    def tempo_total(self):
        if self.data_inicio_reparo and self.data_fim_reparo:
            delta = self.data_fim_reparo - self.data_inicio_reparo
            horas, rem = divmod(delta.seconds, 3600)
            minutos, _ = divmod(rem, 60)
            return f"{delta.days}d {horas}h {minutos}min"
        return "Em execução"

    def __str__(self):
        return f"{self.titulo} ({self.get_categoria_display()})"

class SolicitacaoTroca(models.Model):
    aluno = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    motivo = models.TextField()
    data_solicitacao = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, default='Pendente')

class Comunicado(models.Model):
    TIPOS = [
        ('DENUNCIA', 'Denúncia Anônima'),
        ('COMPORTAMENTO', 'Comportamento Inadequado'),
        ('PERDA', 'Perda de Chave/Cartão'),
    ]
    
    tipo = models.CharField(max_length=20, choices=TIPOS)
    descricao = models.TextField()
    data_envio = models.DateTimeField(auto_now_add=True)
    autor = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Adicionado para Inteligência de Gestão: saber qual quarto está sofrendo a ocorrência/denúncia
    quarto_relacionado = models.ForeignKey(Quarto, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.get_tipo_display()} - {self.data_envio.strftime('%d/%m %H:%M')}"
    
class RegistroAcesso(models.Model):
    TIPOS = [('ENTRADA', 'Entrada'), ('SAIDA', 'Saída')]
    aluno = models.ForeignKey(Usuario, on_delete=models.CASCADE, null=True, blank=True)
    visitante_nome = models.CharField(max_length=100, null=True, blank=True)
    visitante_documento = models.CharField(max_length=20, null=True, blank=True)
    tipo = models.CharField(max_length=10, choices=TIPOS)
    data_hora = models.DateTimeField(auto_now_add=True)

class VistoriaQuarto(models.Model):
    quarto = models.ForeignKey(Quarto, on_delete=models.CASCADE)
    servidor = models.ForeignKey(Usuario, on_delete=models.CASCADE)
    data = models.DateTimeField(auto_now_add=True)
    
    # Checklist
    cama_organizada = models.BooleanField(default=False)
    danos = models.BooleanField(default=False)
    limpeza = models.BooleanField(default=False)
    itens_proibidos = models.BooleanField(default=False)
    
    observacoes = models.TextField(blank=True)
    foto_vistoria = models.ImageField(upload_to='vistorias/', null=True, blank=True)

    def __str__(self):
        return f"Vistoria {self.quarto} - {self.data.strftime('%d/%m/%Y')}"

# --- Novos Modelos Exclusivos para demandas do Gestor ---

class CustoFixoMensal(models.Model):
    """Modelo para acompanhar os custos de água e luz inseridos mensalmente pelo gestor"""
    mes_referencia = models.DateField(help_text="Insira o primeiro dia do mês correspondente (ex: 01/05/2026)")
    consumo_agua = models.DecimalField(max_digits=10, decimal_places=2)
    consumo_luz = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return f"Custos Finais de {self.mes_referencia.strftime('%m/%Y')}"


class AdvertenciaDisciplinar(models.Model):
    """Modelo para tratar a seção '🚨 Disciplina' e controle de reincidência de problemas"""
    aluno = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='advertencias')
    motivo = models.TextField()
    data_emissao = models.DateField(auto_now_add=True)
    gravidade = models.CharField(max_length=10, choices=[('LEVE', 'Leve'), ('MEDIA', 'Média'), ('GRAVE', 'Grave')], default='LEVE')

    def __str__(self):
        return f"Advertência para {self.aluno.username} - {self.data_emissao}"