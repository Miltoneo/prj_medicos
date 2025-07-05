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
from .models import *

# For backward compatibility, expose the app_name
app_name = 'medicos'
