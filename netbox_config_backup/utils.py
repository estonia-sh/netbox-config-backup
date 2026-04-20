import time
import datetime
import difflib
from netmiko import ConnectHandler
from django.contrib import messages
from ncclient import manager
import xmltodict
from rich import status

from .models import DeviceConfigBackup, ConfigBackupRecord, ConfigChange
from dcim.models import Device

def backup_device_config(device: Device, username: str, password: str, device_backup: DeviceConfigBackup,request):
    """
    通过SSH获取设备配置，支持思科、华为、H3C
    """
    # version = Device.objects.filter(pk=device.device_id).device_type
    backup_record = ConfigBackupRecord.objects.create(
        device=device,
        status='failed'
    )
    start_time = time.time()
    device_ip = str(device.primary_ip).split('/')[0]
    device_platform = str(device.platform.name).lower()
    # 通过netmiko获得配置备份
    netmiko_device = {
        "device_type": device_platform,  # 平台slug对应netmiko类型(cisco_ios/huawei等)
        "ip": device_ip,
        "username": username,  # 改为你的设备账号
        "password": password,  # 改为你的设备密码
        "timeout": 10,
    }
    # 通过NETCONF获得配置备份
    # 设备连接参数
    netconf_device = {
        "host": device_ip,  # 设备IP
        "username": username,
        "password": password,
        "port": 22,
        "hostkey_verify": False,
    }
    try:
        with ConnectHandler(**netmiko_device) as conn:
            # 进入特权模式(思科设备)
            if netmiko_device['device_type'] == 'cisco_ios':
                conn.enable()
            # ======================
            # 根据设备类型执行对应命令
            # ======================
            if 'cisco' in netmiko_device['device_type']:
                config = conn.send_command("show running-config")
            elif 'huawei' in netmiko_device['device_type']:
                config = conn.send_command("display current-configuration")
            else:
                config = conn.send_command("show running-config")  # 默认命令
        try:
            config_data_xml = get_config_via_netconf(netconf_device)
            backup_record.config_data_xml = config_data_xml
            device_backup.config_data_xml = config_data_xml
            device_backup.error_msg = ''
        except Exception as e:
            backup_record.error_msg = str(e)
            device_backup.error_msg = str(e)
            if request:
                messages.error(request, f'设备{device.name}执行NETCONF备份失败:{e}')
        # 格式化时间
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        # 5. 保存配置到数据库
        backup_record.filename = f'{device.name}-{now}.cfg'
        backup_record.status = 'success'
        backup_record.config_data_txt = config
        backup_record.backup_time = now

        device_backup.filename = f'{device.name}-{now}.cfg'
        device_backup.status = 'success'
        device_backup.config_data_txt = config
        device_backup.backup_time = now
        device_backup.duration = datetime.timedelta(seconds=time.time() - start_time)
        if request:
            messages.success(request, f"设备 {device.name} 执行SSH配置备份成功！")

    except Exception as e:
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        backup_record.status = 'failed'
        device_backup.status = 'failed'
        backup_record.error_msg = str(e)
        device_backup.error_msg = str(e)
        backup_record.backup_time = now
        device_backup.backup_time = now
        if request:
            messages.error(request,f'设备{device.name}备份失败:{device_backup.error_msg}')

    finally:
        device_backup.save()
        backup_record.save()

    new_backup = backup_record
    # ======================
    # 新增：自动生成变更记录
    # ======================
    try:
        # 获取该设备上一次最新备份
        old_backup = ConfigBackupRecord.objects.filter(
            device=device
        ).exclude(id=new_backup.id).order_by("-id").first()

        if old_backup:
            # 对比新旧配置
            diff_html,status = generate_config_diff(
                old_backup.config_data_txt,
                new_backup.config_data_txt
            )
            # 生成变更记录
            ConfigChange.objects.create(
                device=device,
                old_backup=old_backup,
                new_backup=new_backup,
                diff_content=diff_html,
                status=status,
                change_time=datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                change_summary=f"变更自 {old_backup.backup_time} → {new_backup.backup_time}"
            )
    except Exception as e:
        if request:
            messages.error(request,f'设备{device.name}生成变更失败:{e}')

    return True

def generate_config_diff(old_config, new_config):
    """
    生成配置差异（适配NetBox模板的高亮HTML格式）
    修复：仅生成diff表格，无完整HTML页面，去掉多余图例，处理无差异/首次备份场景
    """
    # 处理空配置（兼容首次备份、空配置场景）
    old_config = old_config or ""
    new_config = new_config or ""

    old_lines = old_config.splitlines()[7:-1]
    new_lines = new_config.splitlines()[7:-1]
    status = 'first_backup'
    # 场景1：首次备份（无旧配置）
    if not old_lines:
        return f'''
        <div class="alert alert-info mb-3">ℹ️ 首次备份，无历史配置，以下为全量配置</div>
        <pre class="bg-light p-3 rounded" style="max-height: 600px; overflow-y: auto; white-space: pre-wrap;">{new_config}</pre>
        ''', status

    # 场景2：配置完全无差异
    if old_lines == new_lines:
        status = 'no_change'
        return '<div class="alert alert-success">✅ 本次备份与上一次配置完全一致，无任何变更</div>', status

    # 创建 difflib 对比器（生成HTML高亮）
    diff = difflib.HtmlDiff(
        wrapcolumn=120,  # 换行宽度
        tabsize=4        # Tab 宽度
    )

    # 生成差异HTML（设置标题，适配NetBox）
    html_diff = diff.make_file(
        fromlines=old_lines,
        tolines=new_lines,
        fromdesc='旧配置',
        todesc='新配置',
        context=True,  # 只显示变更行+上下文（精简展示）
        numlines=5     # 上下文行数
    )
    status = 'changed'
    return html_diff,status


# 1. 获取运行配置（备份）
def get_config_via_netconf(device):
    with manager.connect(**device) as m:
        # 获取 running-config
        netconf_config = m.get_config(source="running").data_xml
        # 转换为可读格式（可选）
        config_dict = xmltodict.parse(netconf_config)

        return netconf_config

# 恢复设备配置
def recovery_via_netconf(device: Device, username: str, password: str, device_backup,request):
    device_ip = str(device.primary_ip).split('/')[0]
    # 通过NETCONF获得配置备份
    # 设备连接参数
    netconf_device = {
        "host": device_ip,  # 设备IP
        "username": username,
        "password": password,
        "port": 22,
        "hostkey_verify": False,
    }
    config_data = device_backup.config_data_xml
    try:
        with manager.connect(**netconf_device) as m:
            # ============== 核心修复 1 ==============
            # 把 <data> 标签替换为 <config>（解决XMLError）
            fixed_config = config_data.replace('<data xmlns', '<config xmlns').replace('</data>', '</config>')

            # ============== 核心修复 2 ==============
            # 移除 default_operation="replace"（老IOS不支持）
            m.edit_config(
                target="running",
                config=fixed_config  # 只用修复后的配置
            )

            # 保存到启动配置
            m.copy_config(source="running", target="startup")

            messages.success(request, f"{device.name}:✅ 配置恢复成功！")

    except Exception as e:
        # 捕获异常，避免500错误
        messages.error(request, f"{device.name}:❌ 恢复失败 - {str(e)}")