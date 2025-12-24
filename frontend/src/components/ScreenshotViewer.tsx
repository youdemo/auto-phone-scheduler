/**
 * 设备屏幕截图查看器
 * 使用定时刷新单张截图来实现实时效果
 */
import { useEffect, useRef, useState } from 'react'
import { devicesApi } from '@/api/client'

interface ScreenshotViewerProps {
  deviceId: string
  className?: string
  refreshInterval?: number // 刷新间隔（毫秒）
}

export function ScreenshotViewer({
  deviceId,
  className,
  refreshInterval = 500, // 默认 2fps，避免请求过于频繁
}: ScreenshotViewerProps) {
  const [imageUrl, setImageUrl] = useState<string>('')
  const [error, setError] = useState<string | null>(null)
  const timeoutRef = useRef<number | null>(null)
  const mountedRef = useRef(true)

  useEffect(() => {
    mountedRef.current = true

    const updateImage = () => {
      if (!mountedRef.current) return
      // 直接更新 URL，让浏览器加载图片
      const url = `${devicesApi.getScreenshotUrl(deviceId)}?t=${Date.now()}`
      setImageUrl(url)
    }

    // 立即获取第一张截图
    updateImage()

    // 设置定时刷新 - 使用 setTimeout 链式调用避免堆积
    const scheduleNext = () => {
      if (!mountedRef.current) return
      timeoutRef.current = window.setTimeout(() => {
        updateImage()
        scheduleNext()
      }, refreshInterval)
    }
    scheduleNext()

    return () => {
      mountedRef.current = false
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
        timeoutRef.current = null
      }
    }
  }, [deviceId, refreshInterval])

  // 图片加载成功时
  const handleLoad = () => {
    setError(null)
  }

  // 图片加载失败时（可能是设备断开）
  const handleError = () => {
    // 不设置错误，继续尝试下一张
  }

  if (error) {
    return (
      <div className={`flex items-center justify-center text-muted-foreground ${className || ''}`}>
        {error}
      </div>
    )
  }

  // 等待第一张截图 URL 生成
  if (!imageUrl) {
    return (
      <div className={`flex items-center justify-center text-muted-foreground ${className || ''}`}>
        加载中...
      </div>
    )
  }

  return (
    <img
      src={imageUrl}
      alt="设备屏幕"
      className={`max-h-full w-auto rounded-lg shadow-lg ${className || ''}`}
      style={{ maxWidth: '280px', objectFit: 'contain' }}
      onLoad={handleLoad}
      onError={handleError}
    />
  )
}
