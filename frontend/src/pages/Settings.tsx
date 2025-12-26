import { useState, useEffect } from 'react'
import { useSearchParams } from 'react-router-dom'
import { toast } from 'sonner'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Switch } from '@/components/ui/switch'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog'
import { settingsApi, devicesApi, notificationsApi, appPackagesApi } from '@/api/client'
import type { NotificationChannel, NotificationChannelCreate, NotificationType, AppPackage, AppPackageCreate } from '@/types'
import {
  RefreshCw,
  Smartphone,
  Save,
  TestTube,
  CheckCircle,
  XCircle,
  Settings as SettingsIcon,
  Bell,
  Package,
  Plus,
  Pencil,
  Trash2,
  Send,
  MessageSquare,
  Wifi,
  Unplug,
  Check,
} from 'lucide-react'

// API 配置组件
function ApiSettings() {
  const queryClient = useQueryClient()
  const [formData, setFormData] = useState({
    autoglm_base_url: '',
    autoglm_api_key: '',
    autoglm_model: '',
    autoglm_max_steps: 100,
  })
  const [remoteAddress, setRemoteAddress] = useState('')

  const { data: settings } = useQuery({
    queryKey: ['settings'],
    queryFn: settingsApi.get,
  })

  const { data: devices = [], isLoading: devicesLoading } = useQuery({
    queryKey: ['devices'],
    queryFn: devicesApi.list,
  })

  const updateMutation = useMutation({
    mutationFn: settingsApi.update,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      toast.success('设置已保存')
    },
  })

  const refreshDevicesMutation = useMutation({
    mutationFn: devicesApi.refresh,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['devices'] })
    },
  })

  const connectDeviceMutation = useMutation({
    mutationFn: devicesApi.connect,
    onSuccess: (data) => {
      if (data.success) {
        toast.success(data.message)
        setRemoteAddress('')
        queryClient.invalidateQueries({ queryKey: ['devices'] })
      } else {
        toast.error(data.message)
      }
    },
    onError: (error: Error) => {
      toast.error(error.message || '连接失败')
    },
  })

  const disconnectDeviceMutation = useMutation({
    mutationFn: devicesApi.disconnect,
    onSuccess: (data) => {
      if (data.success) {
        toast.success(data.message)
        queryClient.invalidateQueries({ queryKey: ['devices'] })
        // 如果断开的是当前选中的设备，清除选择
        if (settings?.selected_device === data.serial) {
          updateMutation.mutate({ selected_device: '' })
        }
      } else {
        toast.error(data.message)
      }
    },
  })

  const selectDeviceMutation = useMutation({
    mutationFn: (serial: string) => settingsApi.update({ selected_device: serial }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['settings'] })
      toast.success('已选择设备')
    },
  })

  const [testResult, setTestResult] = useState<{
    success: boolean
    message: string
    models: string[] | null
  } | null>(null)

  const testMutation = useMutation({
    mutationFn: settingsApi.test,
    onSuccess: (data) => {
      setTestResult(data)
    },
    onError: (error: Error) => {
      setTestResult({
        success: false,
        message: error.message || '测试失败',
        models: null,
      })
    },
  })

  useEffect(() => {
    if (settings) {
      setFormData({
        autoglm_base_url: settings.autoglm_base_url || '',
        autoglm_api_key: '',
        autoglm_model: settings.autoglm_model || '',
        autoglm_max_steps: settings.autoglm_max_steps || 100,
      })
    }
  }, [settings])

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const data: Record<string, string | number> = {}

    if (formData.autoglm_base_url) {
      data.autoglm_base_url = formData.autoglm_base_url
    }
    if (formData.autoglm_api_key) {
      data.autoglm_api_key = formData.autoglm_api_key
    }
    if (formData.autoglm_model) {
      data.autoglm_model = formData.autoglm_model
    }
    if (formData.autoglm_max_steps) {
      data.autoglm_max_steps = formData.autoglm_max_steps
    }

    updateMutation.mutate(data)
  }

  return (
    <div className="space-y-6">
      {/* AutoGLM Settings */}
      <Card>
        <CardHeader>
          <CardTitle>AutoGLM 配置</CardTitle>
          <CardDescription>
            配置 AutoGLM 模型服务的连接参数
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="base_url">API 地址</Label>
              <Input
                id="base_url"
                value={formData.autoglm_base_url}
                onChange={(e) =>
                  setFormData({ ...formData, autoglm_base_url: e.target.value })
                }
                placeholder="https://open.bigmodel.cn/api/paas/v4"
              />
              <p className="text-xs text-muted-foreground">
                智谱: https://open.bigmodel.cn/api/paas/v4
                <br />
                ModelScope: https://api-inference.modelscope.cn/v1
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="api_key">API Key</Label>
              <Input
                id="api_key"
                type="password"
                value={formData.autoglm_api_key}
                onChange={(e) =>
                  setFormData({ ...formData, autoglm_api_key: e.target.value })
                }
                placeholder={settings?.autoglm_api_key ? '已配置 (留空保持不变)' : '输入 API Key'}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="model">模型名称</Label>
              <Input
                id="model"
                value={formData.autoglm_model}
                onChange={(e) =>
                  setFormData({ ...formData, autoglm_model: e.target.value })
                }
                placeholder="glm-4v-flash"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="max_steps">最大步数</Label>
              <Input
                id="max_steps"
                type="number"
                value={formData.autoglm_max_steps}
                onChange={(e) =>
                  setFormData({
                    ...formData,
                    autoglm_max_steps: parseInt(e.target.value) || 100,
                  })
                }
                min={1}
                max={500}
              />
            </div>

            <div className="flex gap-3">
              <Button type="submit" disabled={updateMutation.isPending}>
                <Save className="h-4 w-4 mr-2" />
                保存设置
              </Button>
              <Button
                type="button"
                variant="outline"
                onClick={() => {
                  setTestResult(null)
                  testMutation.mutate()
                }}
                disabled={testMutation.isPending}
              >
                <TestTube className={`h-4 w-4 mr-2 ${testMutation.isPending ? 'animate-pulse' : ''}`} />
                测试连接
              </Button>
            </div>

            {testResult && (
              <div
                className={`p-4 rounded-lg border ${
                  testResult.success
                    ? 'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800'
                    : 'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800'
                }`}
              >
                <div className="flex items-center gap-2 mb-2">
                  {testResult.success ? (
                    <CheckCircle className="h-5 w-5 text-green-600 dark:text-green-400" />
                  ) : (
                    <XCircle className="h-5 w-5 text-red-600 dark:text-red-400" />
                  )}
                  <span
                    className={`font-medium ${
                      testResult.success
                        ? 'text-green-700 dark:text-green-300'
                        : 'text-red-700 dark:text-red-300'
                    }`}
                  >
                    {testResult.message}
                  </span>
                </div>
                {testResult.models && testResult.models.length > 0 && (
                  <div className="mt-2">
                    <span className="text-sm text-muted-foreground">可用模型: </span>
                    <div className="flex flex-wrap gap-1 mt-1">
                      {testResult.models.map((model) => (
                        <Badge key={model} variant="secondary" className="text-xs">
                          {model}
                        </Badge>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}
          </form>
        </CardContent>
      </Card>

      {/* Device Management */}
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>设备管理</CardTitle>
              <CardDescription>
                选择用于执行任务的 Android 设备，支持 USB 和 WiFi 连接
              </CardDescription>
            </div>
            <Button
              variant="outline"
              onClick={() => refreshDevicesMutation.mutate()}
              disabled={refreshDevicesMutation.isPending}
            >
              <RefreshCw
                className={`h-4 w-4 mr-2 ${
                  refreshDevicesMutation.isPending ? 'animate-spin' : ''
                }`}
              />
              刷新
            </Button>
          </div>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* 远程设备连接 */}
          <div className="flex gap-2">
            <Input
              value={remoteAddress}
              onChange={(e) => setRemoteAddress(e.target.value)}
              placeholder="输入设备 IP 地址，如 192.168.1.100:5555"
              className="flex-1"
            />
            <Button
              variant="outline"
              onClick={() => {
                if (remoteAddress.trim()) {
                  connectDeviceMutation.mutate(remoteAddress.trim())
                }
              }}
              disabled={connectDeviceMutation.isPending || !remoteAddress.trim()}
            >
              <Wifi className={`h-4 w-4 mr-2 ${connectDeviceMutation.isPending ? 'animate-pulse' : ''}`} />
              连接
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">
            WiFi 连接: 确保设备与电脑在同一局域网，并已执行 adb tcpip 5555
          </p>

          {/* 设备列表 */}
          {devicesLoading ? (
            <p className="text-muted-foreground">加载中...</p>
          ) : devices.length === 0 ? (
            <div className="text-center py-8">
              <Smartphone className="h-12 w-12 mx-auto text-muted-foreground mb-4" />
              <p className="text-muted-foreground mb-2">未检测到设备</p>
              <p className="text-sm text-muted-foreground">
                请确保设备已通过 USB 连接并开启 USB 调试，或通过上方输入框连接 WiFi 设备
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              {devices.map((device) => {
                const isSelected = settings?.selected_device === device.serial
                const isOnline = device.status === 'device'
                const isNetworkDevice = device.serial.includes(':') && !device.serial.startsWith('emulator')

                return (
                  <div
                    key={device.serial}
                    className={`flex items-center justify-between p-4 rounded-lg border-2 transition-colors ${
                      isSelected
                        ? 'border-primary bg-primary/5'
                        : 'border-transparent bg-muted/50 hover:bg-muted'
                    }`}
                  >
                    <div className="flex items-center gap-3 flex-1 min-w-0">
                      {isNetworkDevice ? (
                        <Wifi className="h-5 w-5 shrink-0" />
                      ) : (
                        <Smartphone className="h-5 w-5 shrink-0" />
                      )}
                      <div className="min-w-0">
                        <p className="font-medium truncate">
                          {device.model || device.product || device.serial}
                        </p>
                        <p className="text-sm text-muted-foreground truncate">
                          {device.serial}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-2">
                      {isSelected && (
                        <Badge variant="default" className="shrink-0">
                          <Check className="h-3 w-3 mr-1" />
                          已选择
                        </Badge>
                      )}
                      <Badge
                        variant={isOnline ? 'success' : 'secondary'}
                        className="shrink-0"
                      >
                        {isOnline ? '在线' : device.status}
                      </Badge>
                      {isOnline && !isSelected && (
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => selectDeviceMutation.mutate(device.serial)}
                          disabled={selectDeviceMutation.isPending}
                        >
                          选择
                        </Button>
                      )}
                      {isNetworkDevice && (
                        <Button
                          size="sm"
                          variant="ghost"
                          onClick={() => disconnectDeviceMutation.mutate(device.serial)}
                          disabled={disconnectDeviceMutation.isPending}
                          title="断开连接"
                        >
                          <Unplug className="h-4 w-4" />
                        </Button>
                      )}
                    </div>
                  </div>
                )
              })}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

// 通知配置组件
function NotificationSettings() {
  const queryClient = useQueryClient()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingChannel, setEditingChannel] = useState<NotificationChannel | null>(null)
  const [channelType, setChannelType] = useState<NotificationType>('dingtalk')
  const [formData, setFormData] = useState({
    name: '',
    enabled: true,
    webhook: '',
    secret: '',
    bot_token: '',
    chat_id: '',
  })

  const { data: channels = [], isLoading } = useQuery({
    queryKey: ['notifications'],
    queryFn: notificationsApi.list,
  })

  const createMutation = useMutation({
    mutationFn: notificationsApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      closeDialog()
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: Partial<NotificationChannelCreate> }) =>
      notificationsApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
      closeDialog()
    },
  })

  const deleteMutation = useMutation({
    mutationFn: notificationsApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['notifications'] })
    },
  })

  const testMutation = useMutation({
    mutationFn: notificationsApi.test,
    onSuccess: () => {
      toast.success('测试通知发送成功')
    },
    onError: () => {
      toast.error('测试通知发送失败，请检查配置')
    },
  })

  const openCreateDialog = (type: NotificationType) => {
    setEditingChannel(null)
    setChannelType(type)
    setFormData({
      name: type === 'dingtalk' ? '钉钉通知' : 'Telegram通知',
      enabled: true,
      webhook: '',
      secret: '',
      bot_token: '',
      chat_id: '',
    })
    setIsDialogOpen(true)
  }

  const openEditDialog = (channel: NotificationChannel) => {
    setEditingChannel(channel)
    setChannelType(channel.type)
    setFormData({
      name: channel.name,
      enabled: channel.enabled,
      webhook: channel.config.webhook || '',
      secret: channel.config.secret || '',
      bot_token: channel.config.bot_token || '',
      chat_id: channel.config.chat_id || '',
    })
    setIsDialogOpen(true)
  }

  const closeDialog = () => {
    setIsDialogOpen(false)
    setEditingChannel(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    const config: Record<string, string> =
      channelType === 'dingtalk'
        ? { webhook: formData.webhook, secret: formData.secret }
        : { bot_token: formData.bot_token, chat_id: formData.chat_id }

    const data: NotificationChannelCreate = {
      type: channelType,
      name: formData.name,
      config,
      enabled: formData.enabled,
    }

    if (editingChannel) {
      updateMutation.mutate({ id: editingChannel.id, data })
    } else {
      createMutation.mutate(data)
    }
  }

  if (isLoading) {
    return <div className="py-8 text-center text-muted-foreground">加载中...</div>
  }

  return (
    <div className="space-y-4">
      {/* Add Channel Cards */}
      <div className="grid gap-4 md:grid-cols-2">
        <Card
          className="cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => openCreateDialog('dingtalk')}
        >
          <CardContent className="py-6 flex items-center gap-4">
            <div className="p-3 rounded-lg bg-blue-500/10">
              <MessageSquare className="h-6 w-6 text-blue-500" />
            </div>
            <div>
              <h3 className="font-medium">钉钉机器人</h3>
              <p className="text-sm text-muted-foreground">
                通过钉钉群机器人接收通知
              </p>
            </div>
            <Plus className="h-5 w-5 ml-auto text-muted-foreground" />
          </CardContent>
        </Card>

        <Card
          className="cursor-pointer hover:bg-muted/50 transition-colors"
          onClick={() => openCreateDialog('telegram')}
        >
          <CardContent className="py-6 flex items-center gap-4">
            <div className="p-3 rounded-lg bg-sky-500/10">
              <MessageSquare className="h-6 w-6 text-sky-500" />
            </div>
            <div>
              <h3 className="font-medium">Telegram Bot</h3>
              <p className="text-sm text-muted-foreground">
                通过 Telegram Bot 接收通知
              </p>
            </div>
            <Plus className="h-5 w-5 ml-auto text-muted-foreground" />
          </CardContent>
        </Card>
      </div>

      {/* Existing Channels */}
      {channels.length > 0 && (
        <div className="space-y-2">
          <h3 className="text-sm font-medium text-muted-foreground">已配置渠道</h3>
          {channels.map((channel) => (
            <Card key={channel.id}>
              <CardContent className="py-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <MessageSquare className="h-5 w-5" />
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="font-medium">{channel.name}</span>
                        <Badge variant={channel.enabled ? 'success' : 'secondary'}>
                          {channel.enabled ? '启用' : '禁用'}
                        </Badge>
                        <Badge variant="outline">
                          {channel.type === 'dingtalk' ? '钉钉' : 'Telegram'}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-1">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => testMutation.mutate(channel.id)}
                      disabled={testMutation.isPending}
                    >
                      <Send className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => openEditDialog(channel)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        if (confirm('确定要删除这个通知渠道吗？')) {
                          deleteMutation.mutate(channel.id)
                        }
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingChannel ? '编辑通知渠道' : '添加通知渠道'}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="name">渠道名称</Label>
              <Input
                id="name"
                value={formData.name}
                onChange={(e) =>
                  setFormData({ ...formData, name: e.target.value })
                }
                required
              />
            </div>

            {channelType === 'dingtalk' ? (
              <>
                <div className="space-y-2">
                  <Label htmlFor="webhook">Webhook URL</Label>
                  <Input
                    id="webhook"
                    value={formData.webhook}
                    onChange={(e) =>
                      setFormData({ ...formData, webhook: e.target.value })
                    }
                    placeholder="https://oapi.dingtalk.com/robot/send?access_token=xxx"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="secret">签名密钥 (可选)</Label>
                  <Input
                    id="secret"
                    value={formData.secret}
                    onChange={(e) =>
                      setFormData({ ...formData, secret: e.target.value })
                    }
                    placeholder="SEC..."
                  />
                </div>
              </>
            ) : (
              <>
                <div className="space-y-2">
                  <Label htmlFor="bot_token">Bot Token</Label>
                  <Input
                    id="bot_token"
                    value={formData.bot_token}
                    onChange={(e) =>
                      setFormData({ ...formData, bot_token: e.target.value })
                    }
                    placeholder="123456:ABC-DEF..."
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="chat_id">Chat ID</Label>
                  <Input
                    id="chat_id"
                    value={formData.chat_id}
                    onChange={(e) =>
                      setFormData({ ...formData, chat_id: e.target.value })
                    }
                    placeholder="-1001234567890"
                    required
                  />
                </div>
              </>
            )}

            <div className="flex items-center justify-between">
              <Label htmlFor="enabled">启用</Label>
              <Switch
                id="enabled"
                checked={formData.enabled}
                onCheckedChange={(checked) =>
                  setFormData({ ...formData, enabled: checked })
                }
              />
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={closeDialog}>
                取消
              </Button>
              <Button
                type="submit"
                disabled={createMutation.isPending || updateMutation.isPending}
              >
                {editingChannel ? '保存' : '添加'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// APP 包名配置组件
function AppPackageSettings() {
  const queryClient = useQueryClient()
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [editingPackage, setEditingPackage] = useState<AppPackage | null>(null)
  const [formData, setFormData] = useState({
    app_name: '',
    package_name: '',
  })

  const { data: packages = [], isLoading } = useQuery({
    queryKey: ['app-packages'],
    queryFn: appPackagesApi.list,
  })

  const createMutation = useMutation({
    mutationFn: appPackagesApi.create,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['app-packages'] })
      closeDialog()
    },
    onError: (error: Error) => {
      toast.error(error.message || '创建失败')
    },
  })

  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: AppPackageCreate }) =>
      appPackagesApi.update(id, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['app-packages'] })
      closeDialog()
    },
    onError: (error: Error) => {
      toast.error(error.message || '更新失败')
    },
  })

  const deleteMutation = useMutation({
    mutationFn: appPackagesApi.delete,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['app-packages'] })
    },
  })

  const openCreateDialog = () => {
    setEditingPackage(null)
    setFormData({ app_name: '', package_name: '' })
    setIsDialogOpen(true)
  }

  const openEditDialog = (pkg: AppPackage) => {
    setEditingPackage(pkg)
    setFormData({
      app_name: pkg.app_name,
      package_name: pkg.package_name,
    })
    setIsDialogOpen(true)
  }

  const closeDialog = () => {
    setIsDialogOpen(false)
    setEditingPackage(null)
  }

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (editingPackage) {
      updateMutation.mutate({ id: editingPackage.id, data: formData })
    } else {
      createMutation.mutate(formData)
    }
  }

  if (isLoading) {
    return <div className="py-8 text-center text-muted-foreground">加载中...</div>
  }

  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <p className="text-sm text-muted-foreground">
          配置自定义 APP 名称与包名的映射关系，用于 Launch 动作
        </p>
        <Button onClick={openCreateDialog}>
          <Plus className="h-4 w-4 mr-2" />
          添加映射
        </Button>
      </div>

      {packages.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center">
            <p className="text-muted-foreground">暂无自定义 APP 包名映射</p>
          </CardContent>
        </Card>
      ) : (
        <div className="space-y-2">
          {packages.map((pkg) => (
            <Card key={pkg.id}>
              <CardContent className="py-3">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1 min-w-0">
                    <Package className="h-5 w-5 text-muted-foreground shrink-0" />
                    <div className="min-w-0">
                      <div className="font-medium">{pkg.app_name}</div>
                      <div className="text-sm text-muted-foreground truncate">
                        {pkg.package_name}
                      </div>
                    </div>
                  </div>
                  <div className="flex gap-1 ml-2">
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => openEditDialog(pkg)}
                    >
                      <Pencil className="h-4 w-4" />
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      onClick={() => {
                        if (confirm('确定要删除这个映射吗？')) {
                          deleteMutation.mutate(pkg.id)
                        }
                      }}
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* Create/Edit Dialog */}
      <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {editingPackage ? '编辑 APP 包名映射' : '添加 APP 包名映射'}
            </DialogTitle>
          </DialogHeader>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="app_name">APP 名称</Label>
              <Input
                id="app_name"
                value={formData.app_name}
                onChange={(e) =>
                  setFormData({ ...formData, app_name: e.target.value })
                }
                placeholder="如: 某某银行"
                required
              />
              <p className="text-xs text-muted-foreground">
                用于 Launch 动作的应用名称
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="package_name">包名</Label>
              <Input
                id="package_name"
                value={formData.package_name}
                onChange={(e) =>
                  setFormData({ ...formData, package_name: e.target.value })
                }
                placeholder="如: com.example.app"
                required
              />
              <p className="text-xs text-muted-foreground">
                Android 应用包名，可通过 adb shell pm list packages 查看
              </p>
            </div>

            <DialogFooter>
              <Button type="button" variant="outline" onClick={closeDialog}>
                取消
              </Button>
              <Button
                type="submit"
                disabled={createMutation.isPending || updateMutation.isPending}
              >
                {editingPackage ? '保存' : '添加'}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </div>
  )
}

export function Settings() {
  const [searchParams, setSearchParams] = useSearchParams()
  const currentTab = searchParams.get('tab') || 'api'

  const handleTabChange = (value: string) => {
    setSearchParams({ tab: value })
  }

  return (
    <div className="space-y-6 h-full flex flex-col">
      <h1 className="text-3xl font-bold">系统设置</h1>

      <Tabs value={currentTab} onValueChange={handleTabChange} className="flex-1 flex flex-col min-h-0">
        <TabsList>
          <TabsTrigger value="api">
            <SettingsIcon className="h-4 w-4 mr-2" />
            API 配置
          </TabsTrigger>
          <TabsTrigger value="notifications">
            <Bell className="h-4 w-4 mr-2" />
            通知配置
          </TabsTrigger>
          <TabsTrigger value="packages">
            <Package className="h-4 w-4 mr-2" />
            APP 包名
          </TabsTrigger>
        </TabsList>
        <TabsContent value="api" className="flex-1 overflow-auto">
          <ApiSettings />
        </TabsContent>
        <TabsContent value="notifications" className="flex-1 overflow-auto">
          <NotificationSettings />
        </TabsContent>
        <TabsContent value="packages" className="flex-1 overflow-auto">
          <AppPackageSettings />
        </TabsContent>
      </Tabs>
    </div>
  )
}
