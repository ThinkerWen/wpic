import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  // 状态
  const token = ref(localStorage.getItem('wpic_token') || '')
  const user = ref(null)
  const isLoading = ref(false)

  // 计算属性
  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'admin')

  // 保存 token 到 localStorage
  const saveToken = (newToken) => {
    token.value = newToken
    localStorage.setItem('wpic_token', newToken)
  }

  // 清除 token
  const clearToken = () => {
    token.value = ''
    localStorage.removeItem('wpic_token')
  }

  // 登录
  const login = async (username, password) => {
    try {
      isLoading.value = true
      const response = await authAPI.login(username, password)
      
      if (response.data.access_token) {
        saveToken(response.data.access_token)
        await getCurrentUser()
        return { success: true }
      } else {
        throw new Error('登录失败：未收到访问令牌')
      }
    } catch (error) {
      console.error('登录失败:', error)
      return {
        success: false,
        message: error.response?.data?.detail || error.message || '登录失败'
      }
    } finally {
      isLoading.value = false
    }
  }

  // 获取当前用户信息
  const getCurrentUser = async () => {
    try {
      const response = await authAPI.getCurrentUser()
      user.value = response.data
      return user.value
    } catch (error) {
      console.error('获取用户信息失败:', error)
      // 如果获取用户信息失败，清除 token
      clearToken()
      user.value = null
      throw error
    }
  }

  // 登出
  const logout = () => {
    clearToken()
    user.value = null
  }

  // 初始化用户信息（如果有 token）
  const initAuth = async () => {
    if (token.value) {
      try {
        await getCurrentUser()
      } catch (error) {
        // 如果 token 无效，清除它
        logout()
      }
    }
  }

  return {
    // 状态
    token,
    user,
    isLoading,
    
    // 计算属性
    isAuthenticated,
    isAdmin,
    
    // 方法
    login,
    logout,
    getCurrentUser,
    initAuth,
  }
})