from netbox.jobs import JobRunner
from dcim.models import Device
from .models import BackupSchedule, DeviceConfigBackup
from .utils import backup_device_config

class ConfigBackupJob(JobRunner):
    """
    配置备份定时任务（NetBox官方JobRunner规范）
    自动支持 interval 循环执行
    """
    class Meta:
        name = "设备配置定时备份"

    def run(self, *args, **kwargs):
        # 从job.object获取定时任务实例（官方标准取值方式）
        schedule = self.job.object
        if not isinstance(schedule, BackupSchedule) or not schedule.enabled:
            return

        # 获取要备份的设备
        if schedule.backup_all:
            devices = Device.objects.all()
        else:
            devices = schedule.devices.all()

        # 执行备份（后台任务无request）
        for device in devices:
            backup_config = DeviceConfigBackup.objects.filter(device=device).first()
            if not backup_config:
                continue

            backup_device_config(
                device=device,
                username=backup_config.ssh_username,
                password=backup_config.ssh_password,
                device_backup=backup_config,
                request=None
            )