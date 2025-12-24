import { clsx, type ClassValue } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}

/**
 * 将 UTC 时间字符串格式化为本地时间
 * 后端存储的是 UTC 时间（datetime.utcnow()），需要转换为本地时间显示
 */
export function formatDateTime(utcDateStr: string | null | undefined): string {
  if (!utcDateStr) return '-'

  // 如果时间字符串没有时区信息，添加 Z 后缀表示 UTC
  let dateStr = utcDateStr
  if (!dateStr.endsWith('Z') && !dateStr.includes('+') && !dateStr.includes('-', 10)) {
    dateStr = dateStr + 'Z'
  }

  return new Date(dateStr).toLocaleString('zh-CN')
}
