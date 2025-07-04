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
from medicos.models import Conta, UsuarioConta

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
        # URLs que não precisam de tenant (login, logout, etc.)
        exempt_urls = [
            reverse('admin:index'),
            reverse('login'),
            reverse('logout'),
            '/select-account/',
            '/static/',
            '/media/',
        ]
        
        # Verifica se a URL atual está na lista de exceções
        if any(request.path.startswith(url) for url in exempt_urls):
            return None
            
        # Se usuário não está autenticado, redireciona para login
        if not request.user.is_authenticated:
            return redirect('login')
            
        # Tenta obter a conta ativa da sessão
        conta_id = request.session.get('conta_ativa_id')
        
        if conta_id:
            try:
                # Verifica se a conta existe e o usuário tem acesso
                conta = Conta.objects.get(id=conta_id)
                usuario_conta = UsuarioConta.objects.get(
                    usuario=request.user, 
                    conta=conta,
                    ativo=True
                )
                
                # Define a conta ativa no request para uso nas views
                request.conta_ativa = conta
                request.usuario_conta = usuario_conta
                
                # Define a conta global para acesso nas views
                _current_account_storage['conta'] = conta
                
                return None
                
            except (Conta.DoesNotExist, UsuarioConta.DoesNotExist):
                # Remove conta inválida da sessão
                del request.session['conta_ativa_id']
                messages.error(request, 'Acesso negado à conta selecionada.')
        
        # Se chegou aqui, precisa selecionar uma conta
        return redirect('auth:select_account')


class LicenseValidationMiddleware(MiddlewareMixin):
    """
    Middleware que valida se a licença da conta está ativa
    """
    
    def process_request(self, request):
        # URLs que não precisam de validação de licença
        exempt_urls = [
            '/admin/',
            '/auth/login/',
            '/auth/logout/',
            '/auth/select-account/',
            '/auth/license-expired/',
            '/static/',
            '/media/',
        ]
        
        if any(request.path.startswith(url) for url in exempt_urls):
            return None
            
        # Verifica se há conta ativa
        if hasattr(request, 'conta_ativa'):
            try:
                conta = request.conta_ativa
                if conta.data_vencimento_licenca and conta.data_vencimento_licenca < timezone.now().date():
                    messages.error(
                        request, 
                        f'Licença da conta {conta.nome} expirou em {conta.data_vencimento_licenca}'
                    )
                    return redirect('auth:license_expired')
            except:
                messages.error(request, 'Licença não encontrada para esta conta.')
                return redirect('auth:license_expired')
        
        return None


class UserLimitMiddleware(MiddlewareMixin):
    """
    Middleware que monitora o limite de usuários por conta
    """
    
    def process_request(self, request):
        if hasattr(request, 'conta_ativa') and request.user.is_authenticated:
            try:
                conta = request.conta_ativa
                usuarios_count = UsuarioConta.objects.filter(
                    conta=conta,
                    ativo=True
                ).count()
                
                limite_usuarios = conta.tipo_licenca.limite_usuarios if conta.tipo_licenca else 1
                
                # Adiciona informações de limite no contexto
                request.license_info = {
                    'usuarios_atual': usuarios_count,
                    'usuarios_limite': limite_usuarios,
                    'usuarios_disponivel': limite_usuarios - usuarios_count,
                    'plano': conta.tipo_licenca.nome if conta.tipo_licenca else 'Básico',
                    'data_expiracao': conta.data_vencimento_licenca
                }
                
            except:
                request.license_info = None
        
        return None
