from django.apps import AppConfig

class AdsRewardsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ads_rewards'
    def ready(self):
        import ads_rewards.signals

