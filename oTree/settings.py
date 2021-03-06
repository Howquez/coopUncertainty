from os import environ

SESSION_CONFIGS = [
    dict(
        name="dPGG",
        display_name="dPGG Replication",
        num_rounds=10,
        num_demo_participants=3,
        risk=0.0,
        app_sequence=["Intro", "dPGG", "Outro"]
    ), dict(
        name="risky_dPGG",
        display_name="dPGG with risk & without instructions",
        num_rounds=10,
        num_demo_participants=3,
        risk=0.33,
        app_sequence=["dPGG", "Outro"]
    ),
]

# if you set a property in SESSION_CONFIG_DEFAULTS, it will be inherited by all configs
# in SESSION_CONFIGS, except those that explicitly override it.
# the session config can be accessed from methods in your apps as self.session.config,
# e.g. self.session.config['participation_fee']

SESSION_CONFIG_DEFAULTS = dict(
    real_world_currency_per_point=0.05, participation_fee=2.00, doc=""
)

# ISO-639 code
# for example: de, fr, ja, ko, zh-hans
LANGUAGE_CODE = "de"

# e.g. EUR, GBP, CNY, JPY
REAL_WORLD_CURRENCY_CODE = "EUR"
USE_POINTS = True

ROOMS = []

ADMIN_USERNAME = 'admin'
# for security, best to set admin password in an environment variable
ADMIN_PASSWORD = environ.get('OTREE_ADMIN_PASSWORD')

DEMO_PAGE_INTRO_HTML = """ """

SECRET_KEY = ''

# if an app is included in SESSION_CONFIGS, you don't need to list it here
INSTALLED_APPS = ['otree']
