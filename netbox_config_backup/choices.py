from utilities.choices import ChoiceSet

class StatusChoices(ChoiceSet):
    SUCCESS = 'success'
    FAILED = 'failed'
    PENDING = 'pending'

    # 备份状态
    CHOICES = (
        (SUCCESS,'成功', 'success'),
        (FAILED,'失败', 'danger'),
        (PENDING,'待备份', 'warning'),
    )

class ChangeStatusChoices(ChoiceSet):
    # ❶ 禁用 Python 关键字，改用规范命名
    CHANGED = 'changed'
    NO_CHANGE = 'no_change'
    FIRST_BACKUP = 'first_backup'

    # ❷ 颜色使用 Bootstrap 合法类名（danger/success/warning）
    CHOICES = (
        (CHANGED, '发生变更', 'danger'),    # 红色
        (NO_CHANGE, '未变更', 'success'),   # 绿色
        (FIRST_BACKUP, '首次备份', 'warning'), # 黄色
    )