from fileinput import filename

import django_tables2 as tables
from netbox.tables import NetBoxTable, columns, ChoiceFieldColumn
from django.urls import reverse
from .models import DeviceConfigBackup, ConfigBackupRecord,ConfigChange,BackupSchedule
from django.utils.html import format_html

# 设备备份列表
class DeviceConfigBackupTable(NetBoxTable):
    """
    配置备份列表表格
    """
    # 设备列（带链接）
    device = tables.Column(
        linkify={
            # 视图名：plugins:你的插件名:deviceconfigbackup（按报错修正）
            'viewname': 'plugins:netbox_config_backup:deviceconfigbackup',
            'args': [tables.A('pk')],  # 关键：用tables.A()取当前行的pk值
        }
    )
    # 状态列（显示样式）
    status = ChoiceFieldColumn()

    class Meta(NetBoxTable.Meta):
        model = DeviceConfigBackup
        fields = (
            'pk', 'device','status', 'backup_time', 'duration'
        )
        default_columns = (
            'device', 'status', 'backup_time', 'duration'
        )

# 配置备份记录列表
class ConfigBackupRecordTable(NetBoxTable):
    device = tables.Column(
        linkify={
            # 视图名：plugins:你的插件名:deviceconfigbackup（按报错修正）
            'viewname': 'plugins:netbox_config_backup:configbackuprecord',
            'args': [tables.A('pk')],  # 关键：用tables.A()取当前行的pk值
        }
    )
    # 状态列（显示样式）
    status = ChoiceFieldColumn()

    class Meta(NetBoxTable.Meta):
        model = ConfigBackupRecord
        fields = (
            'pk', 'device', 'status', 'backup_time', 'filename'
        )
        default_columns = (
            'device', 'status', 'backup_time', 'filename'
        )

# 配置变更列表
class ConfigChangeTable(NetBoxTable):
    device = tables.Column(
        linkify={
            # 视图名：plugins:你的插件名:deviceconfigbackup（按报错修正）
            'viewname': 'plugins:netbox_config_backup:configchange',
            'args': [tables.A('pk')],  # 关键：用tables.A()取当前行的pk值
        }
    )
    # 状态列（显示样式）
    status = ChoiceFieldColumn()

    class Meta(NetBoxTable.Meta):
        model = ConfigChange
        fields = ("id", "device", "change_summary", "change_time", "actions")
        default_columns = ("device", "change_time", "status","change_summary")


# 自动备份列表
class BackupScheduleTable(NetBoxTable):
    """定时备份任务表格（列表页展示）"""
    name = tables.Column(
        linkify={
            # 视图名：plugins:你的插件名:deviceconfigbackup（按报错修正）
            'viewname': 'plugins:netbox_config_backup:configchange',
            'args': [tables.A('pk')],  # 关键：用tables.A()取当前行的pk值
        }
    )
    enabled = columns.BooleanColumn()
    backup_all = columns.BooleanColumn()
    interval_minutes = tables.Column(verbose_name="执行间隔(分钟)")
    actions = columns.ActionsColumn(actions=("edit", "delete"))

    class Meta(NetBoxTable.Meta):
        model = BackupSchedule
        fields = (
            'pk', 'id', 'name', 'enabled', 'backup_all',
            'devices', 'interval_minutes', 'actions'
        )
        default_columns = (
            'name', 'enabled', 'backup_all', 'interval_minutes', 'actions'
        )