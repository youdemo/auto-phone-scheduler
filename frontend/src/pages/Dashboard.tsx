import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { tasksApi, executionsApi, devicesApi } from '@/api/client'
import { formatDateTime } from '@/lib/utils'
import {
  ListTodo,
  CheckCircle,
  XCircle,
  Clock,
  Smartphone
} from 'lucide-react'

export function Dashboard() {
  const { data: tasks = [] } = useQuery({
    queryKey: ['tasks'],
    queryFn: tasksApi.list,
  })

  const { data: executions = [] } = useQuery({
    queryKey: ['executions'],
    queryFn: () => executionsApi.list(undefined, 10),
  })

  const { data: devices = [] } = useQuery({
    queryKey: ['devices'],
    queryFn: devicesApi.list,
  })

  const enabledTasks = tasks.filter(t => t.enabled).length
  const successExecutions = executions.filter(e => e.status === 'success').length
  const failedExecutions = executions.filter(e => e.status === 'failed').length
  const connectedDevices = devices.filter(d => d.status === 'device').length

  const stats = [
    {
      title: '活跃任务',
      value: enabledTasks,
      total: tasks.length,
      icon: ListTodo,
      color: 'text-blue-500'
    },
    {
      title: '成功执行',
      value: successExecutions,
      icon: CheckCircle,
      color: 'text-green-500'
    },
    {
      title: '失败执行',
      value: failedExecutions,
      icon: XCircle,
      color: 'text-red-500'
    },
    {
      title: '连接设备',
      value: connectedDevices,
      icon: Smartphone,
      color: 'text-purple-500'
    },
  ]

  const getStatusBadge = (status: string) => {
    switch (status) {
      case 'success':
        return <Badge variant="success">成功</Badge>
      case 'failed':
        return <Badge variant="destructive">失败</Badge>
      case 'running':
        return <Badge variant="warning">运行中</Badge>
      default:
        return <Badge variant="secondary">等待</Badge>
    }
  }

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">仪表盘</h1>

      {/* Stats Grid */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        {stats.map((stat) => (
          <Card key={stat.title}>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">
                {stat.title}
              </CardTitle>
              <stat.icon className={`h-4 w-4 ${stat.color}`} />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">
                {stat.value}
                {stat.total !== undefined && (
                  <span className="text-sm font-normal text-muted-foreground">
                    /{stat.total}
                  </span>
                )}
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Recent Executions */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Clock className="h-5 w-5" />
            最近执行
          </CardTitle>
        </CardHeader>
        <CardContent>
          {executions.length === 0 ? (
            <p className="text-muted-foreground text-center py-4">
              暂无执行记录
            </p>
          ) : (
            <div className="space-y-3">
              {executions.map((exec) => (
                <div
                  key={exec.id}
                  className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                >
                  <div>
                    <p className="font-medium">{exec.task_name || `任务 #${exec.task_id}`}</p>
                    <p className="text-sm text-muted-foreground">
                      {formatDateTime(exec.started_at)}
                    </p>
                  </div>
                  {getStatusBadge(exec.status)}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Connected Devices */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Smartphone className="h-5 w-5" />
            已连接设备
          </CardTitle>
        </CardHeader>
        <CardContent>
          {devices.length === 0 ? (
            <p className="text-muted-foreground text-center py-4">
              未检测到设备，请确保设备已通过USB连接并开启调试模式
            </p>
          ) : (
            <div className="space-y-3">
              {devices.map((device) => (
                <div
                  key={device.serial}
                  className="flex items-center justify-between p-3 rounded-lg bg-muted/50"
                >
                  <div>
                    <p className="font-medium">{device.model || device.serial}</p>
                    <p className="text-sm text-muted-foreground">
                      {device.serial}
                    </p>
                  </div>
                  <Badge
                    variant={device.status === 'device' ? 'success' : 'secondary'}
                  >
                    {device.status === 'device' ? '已连接' : device.status}
                  </Badge>
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
