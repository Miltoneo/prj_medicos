# -*- coding: utf-8 -*-
"""
Modularized models for the Medical Association Cash Flow System.

This file now imports all models from the modular structure in the 'models' package.
The original monolithic models.py (2200+ lines) has been refactored into specialized modules:

Structure:
- base.py: Core models, users, companies, and constants
- fiscal.py: Tax and invoice models  
- despesas.py: Expense management and rateio models
- financeiro.py: Manual cash flow and balance models
- auditoria.py: Audit and configuration models
- relatorios.py: Consolidated report models

This maintains backward compatibility while improving maintainability and reducing VS Code memory usage.
All Django functionality (migrations, admin, imports) continues to work seamlessly.
"""

# Import all models and constants from the modular structure
from .models.base import *
from .models.fiscal import *
from .models.despesas import *
from .models.financeiro import *
from .models.auditoria import *
from .models.relatorios import *

# app_name is already imported from the modular structure
# No need to redefine it here
