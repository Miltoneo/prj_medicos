"""
Middleware para isolamento de tenant (SaaS Multi-tenancy)
Garante que todos os dados sejam filtrados por conta/tenant
"""
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from django.utils import timezone
from medicos.models import Conta, ContaMembership

# Storage global para a conta atual (thread-safe)
import threading
_current_account_storage = threading.local()


def get_current_account():
    """
    Retorna a conta atualmente ativa no contexto da requisição
    """
    return getattr(_current_account_storage, 'conta', None)


class TenantMiddleware(MiddlewareMixin):
    """
    Middleware que garante o isolamento de dados por tenant (conta)
    
    Funcionalidades:
    1. Verifica se o usuário tem acesso à conta selecionada
    2. Define a conta ativa na sessão
    3. Filtra automaticamente todos os dados por conta
    4. Redireciona para seleção de conta se necessário
    """
    
    def process_request(self, request):
        # URLs que não precisam de tenant (usar caminhos diretos é mais confiável)
        exempt_paths = [
            '/admin/',
            '/medicos/auth/login/',
            '/medicos/auth/logout/',
            '/medicos/auth/select-account/',
            '/medicos/auth/license-expired/',
            '/medicos/auth/register/',
            '/static/',
            '/media/',
            '/favicon.ico',
        ]
        
        # Verifica se a URL atual está na lista de exceções
        if any(request.path.startswith(path) for path in exempt_paths):
            return None
            
        # Se usuário não está autenticado, redireciona para login
        if not request.user.is_authenticated:
            return redirect('/medicos/auth/login/')
            
        # Tenta obter a conta ativa da sessão
        conta_id = request.session.get('conta_ativa_id')
        
        if conta_id:
            try:
                # Verifica se a conta existe e o usuário tem acesso
                conta = Conta.objects.get(id=conta_id)
                usuario_conta = ContaMembership.objects.get(
                    user=request.user, 
                    conta=conta
                )
                
                # Define a conta ativa no request para uso nas views
                request.conta_ativa = conta
                request.usuario_conta = usuario_conta
                
                # Define a conta global para acesso nas views
                _current_account_storage.conta = conta
                
                return None
                
            except (Conta.DoesNotExist, ContaMembership.DoesNotExist):
                # Remove conta inválida da sessão
                if 'conta_ativa_id' in request.session:
                    del request.session['conta_ativa_id']
                messages.error(request, 'Acesso negado à conta selecionada.')
        
        # Se chegou aqui, precisa selecionar uma conta
        return redirect('/medicos/auth/select-account/')


class LicenseValidationMiddleware(MiddlewareMixin):
    """
    Middleware que valida se a licença da conta está ativa
    """
    
    def process_request(self, request):
        # URLs que não precisam de validação de licença
        exempt_paths = [
            '/admin/',
            '/medicos/auth/login/',
            '/medicos/auth/logout/',
            '/medicos/auth/select-account/',
            '/medicos/auth/license-expired/',
            '/static/',
            '/media/',
        ]
        
        if any(request.path.startswith(path) for path in exempt_paths):
            return None
            
        # Verifica se há conta ativa
        if hasattr(request, 'conta_ativa'):
            try:
                conta = request.conta_ativa
                licenca = conta.licenca
                if not licenca.is_valida():
                    messages.error(
                        request, 
                        f'Licença da conta {conta.name} expirou em {licenca.data_fim}'
                    )
                    return redirect('/medicos/auth/license-expired/')
            except:
                messages.error(request, 'Licença não encontrada para esta conta.')
                return redirect('/medicos/auth/license-expired/')
        
        return None


class UserLimitMiddleware(MiddlewareMixin):
    """
    Middleware que monitora o limite de usuários por conta
    """
    
    def process_request(self, request):
        if hasattr(request, 'conta_ativa') and request.user.is_authenticated:
            try:
                conta = request.conta_ativa
                usuarios_count = ContaMembership.objects.filter(
                    conta=conta
                ).count()
                
                try:
                    licenca = conta.licenca
                    limite_usuarios = licenca.limite_usuarios
                    plano = licenca.plano
                    data_expiracao = licenca.data_fim
                except:
                    limite_usuarios = 1
                    plano = 'Básico'
                    data_expiracao = None
                
                # Adiciona informações de limite no contexto
                request.license_info = {
                    'usuarios_atual': usuarios_count,
                    'usuarios_limite': limite_usuarios,
                    'usuarios_disponivel': limite_usuarios - usuarios_count,
                    'plano': plano,
                    'data_expiracao': data_expiracao
                }
                
            except:
                request.license_info = None
        
        return None
