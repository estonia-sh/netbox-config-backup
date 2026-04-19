from netbox.plugins import PluginConfig

class NetBoxConfigBackupConfig(PluginConfig):
    name = 'netbox_config_backup'
    verbose_name = '设备配置备份'
    description = 'NetBox插件，用于设备SSH配置备份与历史管理'
    version = '0.1.0'
    author = 'Estonia'
    author_email = 'estonia@nebox.com'
    base_url = 'config-backup'
    required_settings = []
    default_settings = {}
    min_version = '4.5.0'
    max_version = '5.2.99'
    api_urls = 'netbox_config_backup.api.urls'

    def ready(self):
        super().ready()
        # 注册任务
        from . import jobs

config = NetBoxConfigBackupConfig