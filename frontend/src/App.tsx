import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { Toaster } from 'sonner'
import { Layout } from '@/components/Layout'
import { Dashboard } from '@/pages/Dashboard'
import { Tasks } from '@/pages/Tasks'
import { PromptRules } from '@/pages/PromptRules'
import { ExecutionDetail } from '@/pages/ExecutionDetail'
import { Settings } from '@/pages/Settings'
import { Debug } from '@/pages/Debug'

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 30, // 30 seconds
      refetchOnWindowFocus: false,
    },
  },
})

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="tasks" element={<Tasks />} />
            <Route path="prompt-rules" element={<PromptRules />} />
            <Route path="history" element={<Navigate to="/tasks" replace />} />
            <Route path="history/:id" element={<ExecutionDetail />} />
            <Route path="debug" element={<Debug />} />
            <Route path="notifications" element={<Navigate to="/settings" replace />} />
            <Route path="settings" element={<Settings />} />
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster richColors position="top-center" />
    </QueryClientProvider>
  )
}

export default App
