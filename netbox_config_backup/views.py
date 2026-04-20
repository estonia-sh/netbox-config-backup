import time
import datetime
import difflib
from filecmp import DEFAULT_IGNORES
from venv import create
from django.urls import reverse
from io import BytesIO
from core.utils import delete_rq_job
from rq.exceptions import NoSuchJobError
from django.http import Http404
from django.contrib.contenttypes.models import ContentType
from netmiko import ConnectHandler
from django.contrib import messages
from django.utils.text import slugify
import paramiko
import zipfile
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.generic import View, DetailView, ListView
from netbox.views.generic import ObjectView, ObjectListView,ObjectEditView,ObjectDeleteView,BulkEditView,BulkDeleteView,ObjectChangeLogView
from netbox import object_actions
from dcim.models import Device
from .models import DeviceConfigBackup,ConfigBackupRecord,ConfigChange,BackupSchedule
from .forms import DeviceConfigBackupEditForm,BackupScheduleForm
from .tables import DeviceConfigBackupTable,ConfigBackupRecordTable,ConfigChangeTable,BackupScheduleTable
from .utils import *
from django.contrib.contenttypes.models import ContentType
#from .tasks import execute_scheduled_backup
# ------------------------------
# 插件视图
# ------------------------------
# 备份列表页
class DeviceConfigBackupListView(ObjectListView):
    queryset = DeviceConfigBackup.objects.all()
    table = DeviceConfigBackupTable  # 可自定义tables.py，此处简化
    template_name = 'netbox_config_backup/backup_list.html'
# 编辑/添加设备
class DeviceConfigBackupEditView(ObjectEditView):
    queryset = DeviceConfigBackup.objects.all()
    form = DeviceConfigBackupEditForm
# 删除指定设备
class DeviceConfigBackupDeleteView(ObjectDeleteView):
    queryset = DeviceConfigBackup.objects.all()
    #form = DeviceConfigBackupDeleteForm
# 批量删除设备
class DeviceConfigBackupBulkDeleteView(BulkDeleteView):
    queryset = DeviceConfigBackup.objects.all()
    table = DeviceConfigBackupTable
# 编辑日志
class DeviceConfigBackupChangeLogView(ObjectChangeLogView):
    queryset = DeviceConfigBackup.objects.all()
# 备份详情页
class DeviceConfigBackupView(ObjectView):
    queryset = DeviceConfigBackup.objects.all()
    template_name = 'netbox_config_backup/deviceconfigbackup.html'
    def get_extra_context(self, request, instance):
        # 获取当前设备的所有备份记录
        backup_records = ConfigBackupRecord.objects.filter(
            device=instance.device
        ).restrict(request.user, 'view')
        # 初始化表格
        records_table = ConfigBackupRecordTable(backup_records)
        records_table.configure(request)
        return {
            'backup_records_table': records_table,
        }



# 备份详细记录
class ConfigBackupRecordView(ObjectView):
    queryset = ConfigBackupRecord.objects.all()
    template_name = 'netbox_config_backup/configbackuprecord.html'
    def get_extra_context(self, request, instance):
        # 获取当前设备的所有备份记录
        configchange_record = ConfigChange.objects.filter(
            device=instance.device
        ).restrict(request.user, 'view')
        # 初始化表格
        records_table = ConfigChangeTable(configchange_record)
        records_table.configure(request)
        return {
            'config_change_record': records_table,
        }
# 备份记录列表
class ConfigBackupRecordListView(ObjectListView):
    queryset = ConfigBackupRecord.objects.all()
    table = ConfigBackupRecordTable
# 编辑指定备份记录
class ConfigBackupRecordEditView(ObjectEditView):
    queryset = ConfigBackupRecord.objects.all()
# 删除指定备份记录
class ConfigBackupRecordDeleteView(ObjectDeleteView):
    queryset = ConfigBackupRecord.objects.all()
# 批量删除备份记录
class ConfigBackupRecordBulkDeleteView(BulkDeleteView):
    queryset = ConfigBackupRecord.objects.all()
    table = ConfigBackupRecordTable
# 变更日志记录
class ConfigBackupRecordChangeLogView(ObjectChangeLogView):
    queryset = ConfigBackupRecord.objects.all()

# 变更列表页
class ConfigChangeListView(ObjectListView):
    queryset = ConfigChange.objects.all()
    table = ConfigChangeTable
class ConfigChangeView(ObjectView):
    queryset = ConfigChange.objects.all()
    template_name = "netbox_config_backup/configchange.html"
class ConfigChangeEditView(ObjectEditView):
    queryset = ConfigChange.objects.all()
class ConfigChangeDeleteView(ObjectDeleteView):
    queryset = ConfigChange.objects.all()
class ConfigChangeChangeLogView(ObjectChangeLogView):
    queryset = ConfigChange.objects.all()
class ConfigChangeBulkDeleteView(BulkDeleteView):
    queryset = ConfigChange.objects.all()
    table = ConfigChangeTable

# === 定时备份任务列表 ===
class BackupScheduleListView(ObjectListView):
    queryset = BackupSchedule.objects.all()
    table = BackupScheduleTable
    template_name = "netbox_config_backup/backupschedule_list.html"
    action_buttons = ["add"]
class BackupScheduleView(ObjectView):
    queryset = BackupSchedule.objects.all()
class BackupScheduleChangeLogView(ObjectChangeLogView):
    queryset = BackupSchedule.objects.all()
# === 新增/编辑定时任务 ===
class BackupScheduleEditView(ObjectEditView):
    queryset = BackupSchedule.objects.all()
    form = BackupScheduleForm
    template_name = "netbox_config_backup/backupschedule_edit.html"
# 启动定时任务
class BackupScheduleActionView(View):
    def post(self, request):
        pk_list = request.POST.getlist('pk')
        if not pk_list:
            messages.warning(request, "请选择要操作的定时任务！")
            return redirect('plugins:netbox_config_backup:backupschedule_list')

        from core.models import Job
        from .jobs import ConfigBackupJob
        for pk in pk_list:
            instance = BackupSchedule.objects.get(pk=pk)
            # 切换启用状态
            instance.enabled = not instance.enabled
            instance.save()
            jobs = Job.objects.filter(object_id = pk)
            #jobs = ConfigBackupJob.get_jobs(instance)

            # ==============================================
            # 2. 【关键】逐个停止 Redis 里的真实任务
            # ==============================================
            for job in jobs:
                try:
                    # 调用你提供的函数，删除 RQ 队列任务
                    delete_rq_job(str(job.job_id))
                except (NoSuchJobError, Http404):
                    # 任务不存在就跳过，不报错
                    pass
            jobs.delete()

            # 启用：创建官方标准循环定时任务
            if instance.enabled:
                self._create_scheduled_job(instance, request.user)
                messages.success(request, f"已启用定时任务：{instance.name}")

            # 暂停：删除所有待执行/运行中的任务
            else:
                messages.success(request, f"已暂停定时任务：{instance.name}")

        return redirect('plugins:netbox_config_backup:backupschedule_list')

    def _create_scheduled_job(self, schedule, user):
        """
        【官方规范】创建循环定时任务
        enqueue_once = 幂等创建，避免重复任务
        interval = 自动循环周期（分钟）
        """
        from .jobs import ConfigBackupJob

        # 官方标准：自动处理循环调度，彻底解决只执行一次问题
        ConfigBackupJob.enqueue(
            instance=schedule,          # 绑定你的定时任务实例
            user=user,
            interval=schedule.interval_minutes,  # 循环间隔（官方自动生效）
            queue_name="default"
        )

class BackupScheduleDeleteView(ObjectDeleteView):
    queryset = BackupSchedule.objects.all()
class BackupScheduleBulkDeleteView(BulkDeleteView):
    queryset = BackupSchedule.objects.all()
    table = BackupScheduleTable

# 触发所有设备备份视图
class TriggerBackupView(View):
    def get(self, request):
        device_backups = DeviceConfigBackup.objects.all()
        #device = get_object_or_404(Device, pk=pk)
        #form = DeviceBackupForm(initial={'device': device})
        if device_backups:
            for device_backup in device_backups:
                device = Device.objects.get(pk=device_backup.device_id)
                backup_device_config(
                            device=device,
                            username=device_backup.ssh_username,
                            password=device_backup.ssh_password,
                            device_backup=device_backup,
                            request=request
                        )
        return redirect('plugins:netbox_config_backup:deviceconfigbackup_list')

    def post(self, request):
        # 1. 安全获取 pk 值（推荐：不存在时返回 None，不报错）
        pk_list = request.POST.getlist('pk')
        #print(pk_list)
        # 2. 主键是数字类型，必须转换为整数（数据库ID都是int）
        for pk in pk_list:
        # device = get_object_or_404(Device, pk=pk)
        #form = DeviceBackupForm(request.POST)
            device_backup = DeviceConfigBackup.objects.filter(pk=int(pk)).first()
            if device_backup:
                device = Device.objects.get(pk=device_backup.device_id)
                backup_device_config(
                    device=device,
                    username=device_backup.ssh_username,
                    password=device_backup.ssh_password,
                    device_backup=device_backup,
                    request=request
                )
        return redirect('plugins:netbox_config_backup:deviceconfigbackup_list')

# 单个设备配置下载
class DeviceConfigDownloadView(View):
    def get(self, request, pk):
        device = DeviceConfigBackup.objects.get(pk=pk)
        # device = get_object_or_404(Device, pk=pk)
        # form = DeviceBackupForm(initial={'device': device})
        # 2. 构造下载响应（纯文本配置）
        response = HttpResponse(
            device.config_data_txt,  # 数据库中存储的配置文本
            content_type='text/plain'  # 文件类型：纯文本
        )

        # 3. 设置为【附件下载】，浏览器自动弹出保存框
        # 使用模型中定义的 filename 作为下载文件名
        response['Content-Disposition'] = f'attachment; filename="{device.filename.replace(" ", "_").replace(":", "-")}"'
        # 4. 返回下载文件
        messages.success(request, f"下载{device.filename}完成！")
        return response

# 批量配置下载
class BulkConfigDownloadView(View):
    def post(self,request):
        # 1. 安全获取 pk 值（推荐：不存在时返回 None，不报错）
        pk_list = request.POST.getlist('pk')
        # print(pk_list)
        # 2. 主键是数字类型，必须转换为整数（数据库ID都是int）
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            success_count = 0

            for pk in pk_list:
                try:
                    # 获取备份记录
                    backup = DeviceConfigBackup.objects.get(pk=pk)
                    # 过滤空配置
                    if not backup.config_data_txt:
                        messages.warning(request, f"{backup.filename} 无配置内容，已跳过")
                        continue

                    # 文件名规范化（防止乱码/重复）
                    safe_filename = slugify(backup.filename.replace(" ", "_").replace(":", "-")) + ".cfg"

                    # 将配置写入 ZIP
                    zip_file.writestr(safe_filename, backup.config_data_txt.encode('utf-8'))
                    success_count += 1

                except DeviceConfigBackup.DoesNotExist:
                    messages.error(request, f"ID {pk} 记录不存在，已跳过")
                except Exception as e:
                    messages.error(request, f"处理 {backup.filename} 失败：{str(e)}")

        # 3. 无有效文件时返回
        if success_count == 0:
            messages.error(request, "没有可下载的有效配置文件！")
            return redirect('plugins:netbox_config_backup:deviceconfigbackup_list')

        # 4. 构造 ZIP 下载响应
        zip_buffer.seek(0)
        response = HttpResponse(
            zip_buffer,
            content_type='application/zip'
        )
        down_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(time.time()))
        # 下载的压缩包名称
        response['Content-Disposition'] = 'attachment; filename="device_configs_{}.zip"'.format(down_time)

        messages.success(request, f"批量下载完成，共 {success_count} 个配置文件！")
        return response


# 指定配置下载
class ConfigBackupDownloadView(View):
    def get(self, request, pk):
        device = ConfigBackupRecord.objects.get(pk=pk)
        # device = get_object_or_404(Device, pk=pk)
        # form = DeviceBackupForm(initial={'device': device})
        # 2. 构造下载响应（纯文本配置）
        response = HttpResponse(
            device.config_data_txt,  # 数据库中存储的配置文本
            content_type='text/plain'  # 文件类型：纯文本
        )
        # 3. 设置为【附件下载】，浏览器自动弹出保存框
        # 使用模型中定义的 filename 作为下载文件名
        response['Content-Disposition'] = f'attachment; filename="{device.filename.replace(" ", "_").replace(":", "-")}"'
        # 4. 返回下载文件
        messages.success(request, f"下载{device.filename}完成！")
        return response

# 使用NETCONF进行配置恢复
class DeviceConfigRecoveryView(View):
    def get(self, request, pk):
        backup_device = DeviceConfigBackup.objects.get(pk=pk)
        device = Device.objects.get(pk=backup_device.device_id)
        recovery_via_netconf(device,backup_device.ssh_username,backup_device.ssh_password,backup_device,request)
        return redirect(
            reverse("plugins:netbox_config_backup:deviceconfigbackup", kwargs={"pk": pk})
        )

class ConfigRecoveryView(View):
    def get(self, request, pk):
        config_record = ConfigBackupRecord.objects.get(pk=pk)
        device = Device.objects.get(pk=config_record.device_id)
        device_backup = DeviceConfigBackup.objects.filter(device=device).first()
        recovery_via_netconf(device, device_backup.ssh_username, device_backup.ssh_password, config_record, request)
        return redirect(
            reverse("plugins:netbox_config_backup:configbackuprecord", kwargs={"pk": pk})
        )