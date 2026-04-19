from netbox.plugins import PluginMenuItem, PluginMenuButton,PluginMenu
from .models import DeviceConfigBackup

# 左侧主菜单
# menu_items = (
#     PluginMenuItem(
#         link='plugins:netbox_config_backup:deviceconfigbackup_list',
#         link_text='配置备份',
#         permissions=['netbox_config_backup.view_deviceconfigbackup'],
#     ),
#     PluginMenuItem(
#             link='plugins:netbox_config_backup:configchange_list',
#             link_text='变更列表',
#             permissions=['netbox_config_backup.view_configchange'],
#         ),
# )
menu = PluginMenu(
    label="配置备份",
    groups=(
        ("备份管理", (
            PluginMenuItem(
                link="plugins:netbox_config_backup:deviceconfigbackup_list",
                link_text="设备备份"
            ),
            PluginMenuItem(
                link="plugins:netbox_config_backup:backupschedule_list",
                link_text="定时备份"  # 新增按钮
            ),
        )),
        ("备份记录",(
            PluginMenuItem(
                link="plugins:netbox_config_backup:configbackuprecord_list",
                link_text="备份记录"
            ),
            PluginMenuItem(
                link="plugins:netbox_config_backup:configchange_list",
                link_text="变更记录"
            )
        )),
    )
)
# 设备详情页按钮
# device_buttons = (
#     PluginMenuButton(
#         link='plugins:netbox_config_backup:trigger_backup',
#         title='备份配置',
#         icon_class='mdi-cloud-upload',
#         permissions=['netbox_config_backup.add_deviceconfigbackup'],
#     ),
#     PluginMenuButton(
#         link='plugins:netbox_config_backup:trigger_backup',
#         title='备份配置',
#         icon_class='mdi-cloud-upload',
#         permissions=['netbox_config_backup.add_deviceconfigbackup'],
#     ),
# )