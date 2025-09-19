import request from '@/utils/request'

// 认证相关 API
export const authAPI = {
  // 登录
  login(username, password) {
    const formData = new FormData()
    formData.append('username', username)
    formData.append('password', password)
    
    return request.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded',
      },
    })
  },

  // 获取当前用户信息
  getCurrentUser() {
    return request.get('/auth/me')
  },

  // 刷新 Token
  refreshToken() {
    return request.post('/auth/refresh')
  },
}

// 文件相关 API
export const fileAPI = {
  // 上传文件
  uploadFiles(files, options = {}) {
    const formData = new FormData()
    
    // 添加文件
    files.forEach((file) => {
      formData.append('files', file)
    })
    
    // 添加可选参数
    if (options.rename) {
      formData.append('rename', options.rename)
    }
    if (options.path) {
      formData.append('path', options.path)
    }
    
    return request.post('/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      onUploadProgress: options.onProgress,
    })
  },

  // 获取文件列表
  getFiles(params = {}) {
    return request.get('/files/', { params })
  },

  // 获取文件详情
  getFileDetail(fileId) {
    return request.get(`/files/${fileId}`)
  },

  // 删除文件
  deleteFile(fileId) {
    return request.delete(`/files/${fileId}`)
  },

  // 批量删除文件
  deleteFiles(fileIds) {
    return request.delete('/files/batch', {
      data: { file_ids: fileIds }
    })
  },

  // 获取文件统计信息
  getFileStats() {
    return request.get('/files/stats')
  },
}

// 管理员相关 API
export const adminAPI = {
  // 获取用户列表
  getUsers(params = {}) {
    return request.get('/admin/users', { params })
  },

  // 创建用户
  createUser(userData) {
    return request.post('/admin/users', userData)
  },

  // 更新用户
  updateUser(userId, userData) {
    return request.put(`/admin/users/${userId}`, userData)
  },

  // 删除用户
  deleteUser(userId) {
    return request.delete(`/admin/users/${userId}`)
  },

  // 获取系统统计信息
  getSystemStats() {
    return request.get('/admin/stats')
  },

  // 更新用户存储配置
  updateUserStorage(userId, storageConfig) {
    return request.put(`/admin/users/${userId}/storage`, storageConfig)
  },
}