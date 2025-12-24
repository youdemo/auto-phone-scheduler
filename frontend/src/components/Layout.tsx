import { NavLink, Outlet } from 'react-router-dom'
import {
  LayoutDashboard,
  ListTodo,
  Settings,
  Smartphone,
  FileText,
  Terminal,
} from 'lucide-react'
import { cn } from '@/lib/utils'

const navItems = [
  { to: '/', icon: LayoutDashboard, label: '仪表盘' },
  { to: '/tasks', icon: ListTodo, label: '自动化任务' },
  { to: '/prompt-rules', icon: FileText, label: '提示词模版' },
  { to: '/debug', icon: Terminal, label: '调试控制台' },
  { to: '/settings', icon: Settings, label: '系统设置' },
]

export function Layout() {
  return (
    <div className="h-screen flex overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 bg-sidebar border-r border-sidebar-border shrink-0">
        <div className="p-4">
          <div className="flex items-center gap-2 mb-8">
            <Smartphone className="h-6 w-6" />
            <span className="font-bold text-lg">AutoGLM 调度器</span>
          </div>
          <nav className="space-y-1">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  cn(
                    'flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors',
                    isActive
                      ? 'bg-sidebar-accent text-sidebar-accent-foreground'
                      : 'text-sidebar-foreground hover:bg-sidebar-accent/50'
                  )
                }
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </NavLink>
            ))}
          </nav>
        </div>
      </aside>

      {/* Main content - 使用 flex-col 和固定高度，子页面控制自己的滚动 */}
      <main className="flex-1 p-6 flex flex-col min-h-0 overflow-hidden">
        <Outlet />
      </main>
    </div>
  )
}
