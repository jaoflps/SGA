from types import SimpleNamespace

from django.test import SimpleTestCase
from django.urls import reverse

from .views import is_aluno, is_gestor, is_servidor


class PermissionHelperTests(SimpleTestCase):
    def test_role_helpers_respect_expected_flags(self):
        aluno = SimpleNamespace(is_authenticated=True, tipo='ALUNO', is_active=True, bloqueado=False)
        servidor = SimpleNamespace(
            is_authenticated=True,
            tipo='SERVIDOR',
            is_active=True,
            bloqueado=False,
            aprovado_gestor=True,
        )
        gestor = SimpleNamespace(
            is_authenticated=True,
            tipo='GESTOR',
            is_active=True,
            bloqueado=False,
            is_staff=False,
        )
        bloqueado = SimpleNamespace(is_authenticated=True, tipo='ALUNO', is_active=True, bloqueado=True)

        self.assertTrue(is_aluno(aluno))
        self.assertTrue(is_servidor(servidor))
        self.assertTrue(is_gestor(gestor))
        self.assertFalse(is_aluno(bloqueado))


class ProtectedRouteTests(SimpleTestCase):
    def test_dashboards_redirect_anonymous_users_to_login(self):
        protected_routes = [
            reverse('home_aluno'),
            reverse('home_servidor'),
            reverse('home_gestor'),
            reverse('perfil'),
        ]

        for route in protected_routes:
            with self.subTest(route=route):
                response = self.client.get(route)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('login'), response['Location'])

    def test_post_actions_redirect_anonymous_users_to_login(self):
        protected_actions = [
            reverse('criar_chamado'),
            reverse('solicitar_troca'),
            reverse('enviar_comunicado'),
            reverse('registrar_movimentacao'),
            reverse('realizar_vistoria'),
            reverse('gestor_emitir_advertencia'),
            reverse('gestor_lancar_custos'),
        ]

        for route in protected_actions:
            with self.subTest(route=route):
                response = self.client.post(route)
                self.assertEqual(response.status_code, 302)
                self.assertIn(reverse('login'), response['Location'])
