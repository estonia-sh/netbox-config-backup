from django.urls import path
from . import views,models

app_name = 'netbox_config_backup'

urlpatterns = [
    # 备份列表_deviceconfigbackup
    path('', views.DeviceConfigBackupListView.as_view(), name='deviceconfigbackup_list'),
    path('add', views.DeviceConfigBackupEditView.as_view(), name='deviceconfigbackup_add'),
    path('None', views.DeviceConfigBackupBulkDeleteView.as_view(), name='deviceconfigbackup_bulk_delete'),
    path('<int:pk>/edit', views.DeviceConfigBackupEditView.as_view(), name='deviceconfigbackup_edit'),
    path('<int:pk>/delete', views.DeviceConfigBackupDeleteView.as_view(), name='deviceconfigbackup_delete'),
    path('<int:pk>/changelog', views.DeviceConfigBackupChangeLogView.as_view(), name='deviceconfigbackup_changelog',kwargs={'model': models.DeviceConfigBackup}),
    path('<int:pk>', views.DeviceConfigBackupView.as_view(), name='deviceconfigbackup'),
    # 备份详细记录_configbackuprecord
    path('record/<int:pk>', views.ConfigBackupRecordView.as_view(), name='configbackuprecord'),
    path('record/', views.ConfigBackupRecordListView.as_view(), name='configbackuprecord_list'),
    path('record/None', views.ConfigBackupRecordBulkDeleteView.as_view(), name='configbackuprecord_bulk_delete'),
    path('record/<int:pk>/edit', views.ConfigBackupRecordEditView.as_view(), name='configbackuprecord_edit'),
    path('record/<int:pk>/delete', views.ConfigBackupRecordDeleteView.as_view(), name='configbackuprecord_delete'),
    path('record/<int:pk>/changelog', views.ConfigBackupRecordChangeLogView.as_view(), name='configbackuprecord_changelog',kwargs={'model': models.ConfigBackupRecord}),
    # 触发所有设备备份
    path('backup/', views.TriggerBackupView.as_view(), name='trigger_backup_all'),
    # 批量备份设备
    path('edit/', views.TriggerBackupView.as_view(), name='trigger_backup_edit'),
    # 指定配置文件下载
    path('record/<int:pk>/download/',views.ConfigBackupDownloadView.as_view(), name='configbackuprecord_download'),
    # 最新配置文件下载
    path('<int:pk>/download',views.DeviceConfigDownloadView.as_view(), name='deviceconfigbackup_download'),
    # 配置文件批量下载
    path('download/',views.BulkConfigDownloadView.as_view(), name='bulkconfigbackup_download'),
    # 指定配置恢复
    path('record/<int:pk>/recovery',views.ConfigRecoveryView.as_view(), name='configbackuprecord_recovery'),
    # 最后备份配置恢复
    path('<int:pk>/recovery',views.DeviceConfigRecoveryView.as_view(), name='deviceconfigbackup_recovery'),
    # 配置变更列表
    path('changes/', views.ConfigChangeListView.as_view(), name='configchange_list'),
    path('changes/None', views.ConfigChangeBulkDeleteView.as_view(), name='configchange_bulk_delete'),
    path('changes/<int:pk>', views.ConfigChangeView.as_view(), name='configchange'),
    path('changes/<int:pk>/delete', views.ConfigChangeDeleteView.as_view(), name='configchange_delete'),
    path('changes/<int:pk>/edit', views.ConfigChangeEditView.as_view(), name='configchange_edit'),
    path('changes/<int:pk>/changelog', views.ConfigChangeChangeLogView.as_view(), name='configchange_changelog',kwargs={'model': models.ConfigChange}),
    # 定时备份配置
    path('schedules/', views.BackupScheduleListView.as_view(), name='backupschedule_list'),
    path('schedules/add/', views.BackupScheduleEditView.as_view(), name='backupschedule_add'),
    path('schedules/<int:pk>/edit/', views.BackupScheduleEditView.as_view(), name='backupschedule_edit'),
    path('schedules/<int:pk>/delete/', views.BackupScheduleDeleteView.as_view(), name='backupschedule_delete'),
    path('schedules/<int:pk>/changelog/', views.BackupScheduleChangeLogView.as_view(),name='backupschedule_changelog',kwargs={'model': models.BackupSchedule}),
    path('schedules/<int:pk>',views.BackupScheduleView.as_view(),name='backupschedule'),
    path('schedules/None',views.BackupScheduleBulkDeleteView.as_view(),name='backupschedule_bulk_delete'),
    path('action/',views.BackupScheduleActionView.as_view(),name='backupschedule_action'),

]