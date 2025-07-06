"""
Modelos relacionados a relatórios consolidados

Este módulo estava destinado a conter modelos relacionados à geração de relatórios
consolidados mensais, mas foi simplificado para focar no sistema manual de fluxo de caixa.

O modelo RelatorioConsolidadoMensal foi removido para simplificar o sistema.
Relatórios podem ser gerados dinamicamente através de views e consultas diretas.
"""

from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from .base import Conta

# Este módulo agora serve apenas como placeholder para futuros modelos de relatórios
# que sejam realmente necessários e não redundantes com o sistema principal.
