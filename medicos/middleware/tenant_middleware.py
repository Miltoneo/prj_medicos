"""
Middleware para isolamento de tenant (SaaS Multi-tenancy)
Garante que todos os dados sejam filtrados por conta/tenant
"""
from django.contrib.auth import logout
from django.shortcuts import redirect
from django.urls import reverse
from django.contrib import messages
from django.utils.deprecation import MiddlewareMixin
from .models import Conta, ContaMembership


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
                membership = ContaMembership.objects.get(
                    user=request.user, 
                    conta=conta
                )
                
                # Define a conta ativa no request para uso nas views
                request.conta_ativa = conta
                request.user_role = membership.role
                
                # Define a conta nos modelos para filtro automático
                from .models import SaaSBaseModel
                SaaSBaseModel._current_conta = conta
                
                return None
                
            except (Conta.DoesNotExist, ContaMembership.DoesNotExist):
                # Remove conta inválida da sessão
                del request.session['conta_ativa_id']
                messages.error(request, 'Acesso negado à conta selecionada.')
        
        # Se chegou aqui, precisa selecionar uma conta
        return redirect('select_account')


class LicenseValidationMiddleware(MiddlewareMixin):
    """
    Middleware que valida se a licença da conta está ativa
    """
    
    def process_request(self, request):
        # URLs que não precisam de validação de licença
        exempt_urls = [
            reverse('admin:index'),
            reverse('login'),
            reverse('logout'),
            '/select-account/',
            '/license-expired/',
            '/static/',
            '/media/',
        ]
        
        if any(request.path.startswith(url) for url in exempt_urls):
            return None
            
        # Verifica se há conta ativa
        if hasattr(request, 'conta_ativa'):
            try:
                licenca = request.conta_ativa.licenca
                if not licenca.is_valida():
                    messages.error(
                        request, 
                        f'Licença da conta {request.conta_ativa.name} expirou em {licenca.data_fim}'
                    )
                    return redirect('license_expired')
            except:
                messages.error(request, 'Licença não encontrada para esta conta.')
                return redirect('license_expired')
        
        return None


class UserLimitMiddleware(MiddlewareMixin):
    """
    Middleware que monitora o limite de usuários por conta
    """
    
    def process_request(self, request):
        if hasattr(request, 'conta_ativa') and request.user.is_authenticated:
            try:
                licenca = request.conta_ativa.licenca
                memberships_count = ContaMembership.objects.filter(
                    conta=request.conta_ativa
                ).count()
                
                # Adiciona informações de limite no contexto
                request.license_info = {
                    'usuarios_atual': memberships_count,
                    'usuarios_limite': licenca.limite_usuarios,
                    'usuarios_disponivel': licenca.limite_usuarios - memberships_count,
                    'plano': licenca.plano,
                    'data_expiracao': licenca.data_fim
                }
                
            except:
                request.license_info = None
        
        return None
