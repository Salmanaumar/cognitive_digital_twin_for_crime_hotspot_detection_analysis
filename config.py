import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODELS_DIR = os.path.join(BASE_DIR, 'models')
EXPORTS_DIR = os.path.join(BASE_DIR, 'exports')

SECRET_KEY = os.environ.get('SECRET_KEY', 'cognitive_digital_twin_secret_plum_rose_2026')
SESSION_TIMEOUT_MINUTES = 30

# Visual Palette: Plum and Rose Theme
THEME = {
    'primary_plum': '#3B103F',
    'plum_dark': '#290B2C',
    'plum_light': '#54185A',
    'accent_rose': '#D83B6F',
    'rose_hover': '#C12C5E',
    'rose_light': '#FDF2F5',
    'rose_border': '#F4B8CA',
    'bg_main': '#F8F9FA',
    'card_bg': '#FFFFFF',
    'text_dark': '#1E293B',
    'text_muted': '#64748B',
    'risk_high': '#E11D48',
    'risk_med': '#F59E0B',
    'risk_low': '#10B981'
}

DEFAULT_DATASET = os.path.join(DATA_DIR, 'hyderabad_crime_records.csv')
