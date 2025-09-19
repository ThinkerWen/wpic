import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fileAPI } from '@/api'

export const useFileStore = defineStore('file', () => {
  // 状态
  const files = ref([])
  const currentFile = ref(null)
  const isLoading = ref(false)
  const uploadProgress = ref({})
  const pagination = ref({
    page: 1,
    size: 20,
    total: 0,
    totalPages: 0
  })
  const filters = ref({
    search: '',
    type: '',
    sortBy: 'created_at',
    sortOrder: 'desc'
  })

  // 计算属性
  const totalFiles = computed(() => pagination.value.total)
  const hasFiles = computed(() => files.value.length > 0)
  const isUploading = computed(() => Object.keys(uploadProgress.value).length > 0)

  // 获取文件列表
  const fetchFiles = async (params = {}) => {
    try {
      isLoading.value = true
      const requestParams = {
        page: pagination.value.page,
        size: pagination.value.size,
        ...filters.value,
        ...params
      }

      const response = await fileAPI.getFiles(requestParams)
      
      files.value = response.data.items || []
      pagination.value = {
        page: response.data.page || 1,
        size: response.data.size || 20,
        total: response.data.total || 0,
        totalPages: response.data.pages || 0
      }

      return response.data
    } catch (error) {
      console.error('获取文件列表失败:', error)
      throw error
    } finally {
      isLoading.value = false
    }
  }

  // 上传文件
  const uploadFiles = async (fileList, options = {}) => {
    const uploadId = Date.now().toString()
    
    try {
      // 初始化上传进度
      uploadProgress.value[uploadId] = {
        files: fileList.map(file => ({
          name: file.name,
          size: file.size,
          progress: 0
        })),
        totalProgress: 0,
        status: 'uploading'
      }

      const response = await fileAPI.uploadFiles(fileList, {
        ...options,
        onProgress: (progressEvent) => {
          const progress = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          if (uploadProgress.value[uploadId]) {
            uploadProgress.value[uploadId].totalProgress = progress
          }
        }
      })

      // 上传成功
      uploadProgress.value[uploadId].status = 'success'
      
      // 刷新文件列表
      await fetchFiles()
      
      // 清除上传进度（延迟清除以显示成功状态）
      setTimeout(() => {
        delete uploadProgress.value[uploadId]
      }, 2000)

      return response.data
    } catch (error) {
      // 上传失败
      if (uploadProgress.value[uploadId]) {
        uploadProgress.value[uploadId].status = 'error'
        uploadProgress.value[uploadId].error = error.response?.data?.detail || error.message
      }
      
      console.error('文件上传失败:', error)
      throw error
    }
  }

  // 删除文件
  const deleteFile = async (fileId) => {
    try {
      await fileAPI.deleteFile(fileId)
      // 从列表中移除文件
      files.value = files.value.filter(file => file.id !== fileId)
      // 更新总数
      pagination.value.total -= 1
      return true
    } catch (error) {
      console.error('删除文件失败:', error)
      throw error
    }
  }

  // 批量删除文件
  const deleteFiles = async (fileIds) => {
    try {
      await fileAPI.deleteFiles(fileIds)
      // 从列表中移除文件
      files.value = files.value.filter(file => !fileIds.includes(file.id))
      // 更新总数
      pagination.value.total -= fileIds.length
      return true
    } catch (error) {
      console.error('批量删除文件失败:', error)
      throw error
    }
  }

  // 设置当前文件
  const setCurrentFile = (file) => {
    currentFile.value = file
  }

  // 更新过滤器
  const updateFilters = (newFilters) => {
    filters.value = { ...filters.value, ...newFilters }
    pagination.value.page = 1 // 重置到第一页
  }

  // 更新分页
  const updatePagination = (newPagination) => {
    pagination.value = { ...pagination.value, ...newPagination }
  }

  // 清除上传进度
  const clearUploadProgress = (uploadId) => {
    if (uploadId) {
      delete uploadProgress.value[uploadId]
    } else {
      uploadProgress.value = {}
    }
  }

  // 重置状态
  const reset = () => {
    files.value = []
    currentFile.value = null
    isLoading.value = false
    uploadProgress.value = {}
    pagination.value = {
      page: 1,
      size: 20,
      total: 0,
      totalPages: 0
    }
    filters.value = {
      search: '',
      type: '',
      sortBy: 'created_at',
      sortOrder: 'desc'
    }
  }

  return {
    // 状态
    files,
    currentFile,
    isLoading,
    uploadProgress,
    pagination,
    filters,
    
    // 计算属性
    totalFiles,
    hasFiles,
    isUploading,
    
    // 方法
    fetchFiles,
    uploadFiles,
    deleteFile,
    deleteFiles,
    setCurrentFile,
    updateFilters,
    updatePagination,
    clearUploadProgress,
    reset,
  }
})