from rest_framework import serializers
from netbox.api.serializers import NetBoxModelSerializer
# 核心修复：导入Device模型
from dcim.models import Device
from dcim.api.serializers import DeviceSerializer

from ..models import (
    DeviceConfigBackup, ConfigBackupRecord, ConfigChange, BackupSchedule
)
from ..choices import StatusChoices, ChangeStatusChoices


# ------------------------------------------------------------------------------
# 🔥 核心修复：继承基础序列化器，关闭自动URL字段
# ------------------------------------------------------------------------------
class BaseNetBoxSerializer(NetBoxModelSerializer):
    """基础序列化器：禁用自动生成的url超链接字段，杜绝报错"""

    class Meta:
        abstract = True
        # 禁用自动URL字段（根本解决超链接报错）
        fields = ['id', 'created', 'last_updated']


# 1. 设备配置备份序列化器
class DeviceConfigBackupSerializer(BaseNetBoxSerializer):
    device = DeviceSerializer(nested=True, read_only=True)
    device_id = serializers.IntegerField(write_only=True)
    ssh_password = serializers.CharField(write_only=True, required=False, allow_null=True)

    class Meta(BaseNetBoxSerializer.Meta):
        model = DeviceConfigBackup
        fields = BaseNetBoxSerializer.Meta.fields + [
            'device', 'device_id', 'status', 'backup_time',
            'ssh_username', 'ssh_password', 'config_data_txt', 'config_data_xml',
            'error_msg', 'duration', 'filename'
        ]


# 2. 备份记录序列化器
class ConfigBackupRecordSerializer(BaseNetBoxSerializer):
    device = DeviceSerializer(nested=True, read_only=True)
    device_id = serializers.IntegerField(write_only=True)

    class Meta(BaseNetBoxSerializer.Meta):
        model = ConfigBackupRecord
        fields = BaseNetBoxSerializer.Meta.fields + [
            'device', 'device_id', 'filename', 'config_data_txt',
            'config_data_xml', 'status', 'backup_time'
        ]


# 3. 配置变更序列化器
class ConfigChangeSerializer(BaseNetBoxSerializer):
    device = DeviceSerializer(nested=True, read_only=True)
    old_backup = ConfigBackupRecordSerializer(nested=True, read_only=True, allow_null=True)
    new_backup = ConfigBackupRecordSerializer(nested=True, read_only=True)

    device_id = serializers.IntegerField(write_only=True)
    old_backup_id = serializers.IntegerField(write_only=True, allow_null=True)
    new_backup_id = serializers.IntegerField(write_only=True)

    class Meta(BaseNetBoxSerializer.Meta):
        model = ConfigChange
        fields = BaseNetBoxSerializer.Meta.fields + [
            'device', 'device_id', 'old_backup', 'old_backup_id',
            'new_backup', 'new_backup_id', 'diff_content', 'change_summary',
            'change_time', 'status'
        ]


# 4. 定时备份任务序列化器
class BackupScheduleSerializer(BaseNetBoxSerializer):
    devices = DeviceSerializer(nested=True, many=True, read_only=True)
    device_ids = serializers.PrimaryKeyRelatedField(
        queryset=Device.objects.all(), many=True, write_only=True, required=False
    )

    class Meta(BaseNetBoxSerializer.Meta):
        model = BackupSchedule
        fields = BaseNetBoxSerializer.Meta.fields + [
            'name', 'enabled', 'backup_all', 'devices', 'device_ids', 'interval_minutes'
        ]