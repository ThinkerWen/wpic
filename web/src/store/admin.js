import { defineStore } from 'pinia'
import { ref } from 'vue'
import { adminAPI } from '@/api'

export const useAdminStore = defineStore('admin', () => {
  // 状态
  const users = ref([])
  const systemStats = ref({})
  const isLoading = ref(false)

  // 获取用户列表
  const fetchUsers = async (params = {}) => {
    try {
      isLoading.value = true
      const response = await adminAPI.getUsers(params)
      users.value = response.data.items || response.data || []
      return response.data
    } catch (error) {
      console.error('获取用户列表失败:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // 创建用户
  const createUser = async (userData) => {
    try {
      const response = await adminAPI.createUser(userData)
      // 添加到本地列表
      users.value.unshift(response.data)
      return response.data
    } catch (error) {
      console.error('创建用户失败:', error)
      throw error
    }
  }

  // 更新用户
  const updateUser = async (userId, userData) => {
    try {
      const response = await adminAPI.updateUser(userId, userData)
      // 更新本地列表
      const index = users.value.findIndex(user => user.id === userId)
      if (index !== -1) {
        users.value[index] = response.data
      }
      return response.data
    } catch (error) {
      console.error('更新用户失败:', error)
      throw error
    }
  }

  // 删除用户
  const deleteUser = async (userId) => {
    try {
      await adminAPI.deleteUser(userId)
      // 从本地列表移除
      users.value = users.value.filter(user => user.id !== userId)
      return true
    } catch (error) {
      console.error('删除用户失败:', error)
      throw error
    }
  }

  // 更新用户存储配置
  const updateUserStorage = async (userId, storageConfig) => {
    try {
      const response = await adminAPI.updateUserStorage(userId, storageConfig)
      // 更新本地用户信息
      const user = users.value.find(u => u.id === userId)
      if (user) {
        user.storage_config = response.data.storage_config
      }
      return response.data
    } catch (error) {
      console.error('更新用户存储配置失败:', error)
      throw error
    }
  }

  // 获取系统统计信息
  const fetchSystemStats = async () => {
    try {
      const response = await adminAPI.getSystemStats()
      systemStats.value = response.data
      return response.data
    } catch (error) {
      console.error('获取系统统计失败:', error)
      throw error
    }
  }

  // 重置状态
  const reset = () => {
    users.value = []
    systemStats.value = {}
    isLoading.value = false
  }

  return {
    // 状态
    users,
    systemStats,
    isLoading,
    
    // 方法
    fetchUsers,
    createUser,
    updateUser,
    deleteUser,
    updateUserStorage,
    fetchSystemStats,
    reset,
  }
})