import axios from 'axios'
import { useAuthStore } from '@/store/auth'
import router from '@/router'

// 创建 axios 实例
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器
apiClient.interceptors.request.use(
  (config) => {
    const authStore = useAuthStore()
    const token = authStore.token
    
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
apiClient.interceptors.response.use(
  (response) => {
    return response
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      
      switch (status) {
        case 401:
          // Token 过期或无效，清除用户信息并跳转到登录页
          const authStore = useAuthStore()
          authStore.logout()
          router.push('/login')
          break
        case 403:
          // 权限不足
          console.error('权限不足:', data.detail || '无权限访问')
          break
        case 404:
          console.error('资源不存在:', data.detail || '请求的资源不存在')
          break
        case 500:
          console.error('服务器错误:', data.detail || '服务器内部错误')
          break
        default:
          console.error('请求错误:', data.detail || error.message)
      }
    } else if (error.request) {
      // 网络错误
      console.error('网络错误:', '请检查网络连接')
    } else {
      console.error('请求配置错误:', error.message)
    }
    
    return Promise.reject(error)
  }
)

export default apiClient