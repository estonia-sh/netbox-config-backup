from django.db import models
from django.urls import reverse
from netaddr.ip import IPAddress
from netbox.models import NetBoxModel
from dcim.models import Device
from ipam.models import IPAddress
from users.models import User
from utilities.choices import ChoiceSet
from netbox.models.features import JobsMixin
from .choices import StatusChoices,ChangeStatusChoices

class DeviceConfigBackup(NetBoxModel):
    # 关联设备
    device = models.ForeignKey(
        to=Device,
        on_delete=models.CASCADE,
        related_name='config_backups'
    )
    status = models.CharField(
        max_length=20,
        choices=StatusChoices,
        default='pending'
    )
    backup_time = models.CharField(blank=True,null=True,max_length=50)
    ssh_username = models.CharField(blank=True, null=True,max_length=20)
    ssh_password = models.CharField(blank=True, null=True,max_length=100)
    # 配置内容
    config_data_txt = models.TextField(blank=True, null=True, verbose_name="配置内容")
    config_data_xml = models.TextField(blank=True,null=True)
    # 失败原因
    error_msg = models.TextField(blank=True, null=True, verbose_name="错误信息")
    # 备份耗时
    duration = models.DurationField(blank=True, null=True, verbose_name="耗时")
    filename = models.CharField(
        max_length=255,
        verbose_name='File Name',
        help_text='Name of the configuration file (e.g. switch_running.cfg)',
        null = True,
        blank = True
    )
    class Meta:
        ordering = ['-created']
        verbose_name = "备份信息"
        verbose_name_plural = "备份设备列表"

    def __str__(self):
        return f"{self.device.name}"

    def get_absolute_url(self):
         return reverse('plugins:netbox_config_backup:deviceconfigbackup',args=[self.pk])

    def get_status_color(self):
        return StatusChoices.colors.get(self.status)


class ConfigBackupRecord(NetBoxModel):
    """
    配置备份模型，存储设备配置并支持下载
    """
    # 关联设备（必填）
    device = models.ForeignKey(
        to=Device,
        on_delete=models.CASCADE,
        related_name='backup_records',
        verbose_name='Device'
    )
    # 配置文件名（用于下载）
    filename = models.CharField(
        max_length=255,
        verbose_name='File Name',
        help_text='Name of the configuration file (e.g. switch_running.cfg)'
    )
    # 配置内容（核心备份数据）
    config_data_txt = models.TextField(
        verbose_name='Configuration Data',
        help_text='Full configuration text to be stored and downloadable'
    )
    config_data_xml = models.TextField(
        verbose_name='Configuration Data XML',
    )

    status = models.CharField(
        max_length=20,
        choices=StatusChoices,
        default='pending'
    )
    # 失败原因
    error_msg = models.TextField(blank=True, null=True, verbose_name="错误信息")
    backup_time = models.CharField(blank=True,null=True,max_length=50)
    class Meta:
        ordering = ('-created',)
        verbose_name = '设备备份记录'
        verbose_name_plural = '备份信息'

    def __str__(self):
        return f"{self.device.name}"

    def get_absolute_url(self):
         return reverse('plugins:netbox_config_backup:configbackuprecord',args=[self.pk])

    def get_status_color(self):
        return StatusChoices.colors.get(self.status)

    # 下载链接（用于 NetBox UI）
    # def get_download_url(self):
    #     return reverse('plugins:your_plugin_name:configbackup-download', args=[self.pk])

class ConfigChange(NetBoxModel):
    """配置变更记录：自动对比两次备份的差异"""
    device = models.ForeignKey(
        Device, on_delete=models.CASCADE, related_name="config_changes"
    )
    # 上一次备份（旧配置）
    old_backup = models.ForeignKey(
        ConfigBackupRecord, on_delete=models.CASCADE, related_name="changes_as_old", null=True
    )
    # 最新备份（新配置）
    new_backup = models.ForeignKey(
        ConfigBackupRecord, on_delete=models.CASCADE, related_name="changes_as_new"
    )
    # 变更差异内容（高亮HTML格式）
    diff_content = models.TextField(verbose_name="配置差异")
    # 变更摘要
    change_summary = models.CharField(max_length=255, verbose_name="变更摘要")
    # 变更时间
    change_time = models.CharField(blank=True, null=True, max_length=50)
    status = models.CharField(
        max_length=20,
        choices=ChangeStatusChoices,
        default='first_backup',
    )

    class Meta:
        ordering = ["-id"]
        verbose_name = "配置变更"
        verbose_name_plural = "配置变更列表"

    def __str__(self):
        return f"{self.device.name} - 变更记录 {self.change_time}"

    def get_absolute_url(self):
         return reverse('plugins:netbox_config_backup:configchange',args=[self.pk])

    def get_status_color(self):
        return ChangeStatusChoices.colors.get(self.status)

class BackupSchedule(JobsMixin,NetBoxModel):
    """定时备份配置模型（界面配置用）"""
    name = models.CharField(max_length=100, verbose_name="任务名称")
    enabled = models.BooleanField(default=False, verbose_name="启用任务")
    # 备份范围：全部设备 / 指定设备
    backup_all = models.BooleanField(default=True, verbose_name="备份所有设备")
    devices = models.ManyToManyField(
        Device, blank=True, verbose_name="指定备份设备",
        help_text="仅取消「备份所有设备」时生效"
    )
    # 循环间隔（分钟）：例如 60 = 每小时，1440 = 每天
    interval_minutes = models.PositiveIntegerField(
        default=1440, verbose_name="循环间隔（分钟）",
        help_text="例如：60=每小时，1440=每天"
    )
    class Meta:
        verbose_name = "定时备份任务"
        verbose_name_plural = "定时备份任务"

    def __str__(self):
        return self.name

    def get_absolute_url(self):
         return reverse('plugins:netbox_config_backup:backupschedule_list')