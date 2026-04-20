from netbox.api.routers import NetBoxRouter

router = NetBoxRouter()
# 空路由即可，仅用于注册API（不影响功能）
urlpatterns = router.urls