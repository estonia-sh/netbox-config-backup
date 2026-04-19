from django import forms
from netbox.forms import NetBoxModelForm
from utilities.forms.fields import DynamicModelChoiceField
from django.utils.translation import gettext_lazy as _
from dcim.models import Device,DeviceRole,DeviceType
from ipam.models import IPAddress
from .models import DeviceConfigBackup,BackupSchedule

# 编辑设备表单
class DeviceConfigBackupEditForm(NetBoxModelForm):
    device = DynamicModelChoiceField(
        label=_('设备'),
        queryset=Device.objects.all(),
        required=True,
        help_text=_('选择需要执行备份的网络设备')
    )

    ssh_username = forms.CharField(label="SSH用户名", required=True)
    ssh_password = forms.CharField(label="SSH密码", widget=forms.PasswordInput, required=True)

    class Meta:
        model = DeviceConfigBackup
        fields = [
            'device',
            'ssh_username',
            'ssh_password',
        ]

class BackupScheduleForm(forms.ModelForm):
    class Meta:
        model = BackupSchedule
        fields = ['name', 'backup_all', 'devices', 'interval_minutes']
        help_texts = {
            'interval_minutes': '1440 = 每日，60 = 每小时，30 = 每30分钟'
        }