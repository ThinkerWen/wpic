<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div>
      <h1 class="text-2xl font-semibold text-gray-900">系统设置</h1>
      <p class="mt-1 text-sm text-gray-600">管理用户和系统配置</p>
    </div>

    <!-- 系统统计 -->
    <div class="bg-white shadow rounded-lg">
      <div class="px-4 py-5 sm:p-6">
        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">系统统计</h3>
        <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
          <div class="bg-gray-50 overflow-hidden shadow rounded-lg">
            <div class="p-5">
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <UsersIcon class="h-6 w-6 text-gray-400" />
                </div>
                <div class="ml-5 w-0 flex-1">
                  <dl>
                    <dt class="text-sm font-medium text-gray-500 truncate">总用户数</dt>
                    <dd class="text-lg font-medium text-gray-900">{{ adminStore.users.length }}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
          
          <div class="bg-gray-50 overflow-hidden shadow rounded-lg">
            <div class="p-5">
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <PhotoIcon class="h-6 w-6 text-gray-400" />
                </div>
                <div class="ml-5 w-0 flex-1">
                  <dl>
                    <dt class="text-sm font-medium text-gray-500 truncate">总图片数</dt>
                    <dd class="text-lg font-medium text-gray-900">{{ systemStats.totalFiles || 0 }}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
          
          <div class="bg-gray-50 overflow-hidden shadow rounded-lg">
            <div class="p-5">
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <ServerIcon class="h-6 w-6 text-gray-400" />
                </div>
                <div class="ml-5 w-0 flex-1">
                  <dl>
                    <dt class="text-sm font-medium text-gray-500 truncate">存储使用</dt>
                    <dd class="text-lg font-medium text-gray-900">{{ systemStats.totalSize || '0 B' }}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
          
          <div class="bg-gray-50 overflow-hidden shadow rounded-lg">
            <div class="p-5">
              <div class="flex items-center">
                <div class="flex-shrink-0">
                  <ChartBarIcon class="h-6 w-6 text-gray-400" />
                </div>
                <div class="ml-5 w-0 flex-1">
                  <dl>
                    <dt class="text-sm font-medium text-gray-500 truncate">今日上传</dt>
                    <dd class="text-lg font-medium text-gray-900">{{ systemStats.todayUploads || 0 }}</dd>
                  </dl>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 用户管理 -->
    <div class="bg-white shadow rounded-lg">
      <div class="px-4 py-5 sm:p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg leading-6 font-medium text-gray-900">用户管理</h3>
          <button
            @click="showCreateUser = true"
            class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
          >
            <PlusIcon class="h-4 w-4 mr-2" />
            新增用户
          </button>
        </div>

        <!-- 用户表格 -->
        <div class="overflow-hidden shadow ring-1 ring-black ring-opacity-5 md:rounded-lg">
          <table class="min-w-full divide-y divide-gray-300">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">用户</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">角色</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">存储类型</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">创建时间</th>
                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">状态</th>
                <th class="relative px-6 py-3"><span class="sr-only">操作</span></th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="user in adminStore.users" :key="user.id">
                <td class="px-6 py-4 whitespace-nowrap">
                  <div class="flex items-center">
                    <div class="h-10 w-10 flex-shrink-0">
                      <div class="h-10 w-10 rounded-full bg-primary-600 flex items-center justify-center">
                        <span class="text-sm font-medium text-white">
                          {{ user.username.charAt(0).toUpperCase() }}
                        </span>
                      </div>
                    </div>
                    <div class="ml-4">
                      <div class="text-sm font-medium text-gray-900">{{ user.username }}</div>
                      <div class="text-sm text-gray-500">{{ user.email || '未设置邮箱' }}</div>
                    </div>
                  </div>
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span
                    class="inline-flex px-2 py-1 text-xs font-semibold rounded-full"
                    :class="user.role === 'admin' ? 'bg-purple-100 text-purple-800' : 'bg-green-100 text-green-800'"
                  >
                    {{ user.role === 'admin' ? '管理员' : '普通用户' }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {{ user.storage_type || 'local' }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                  {{ formatDateTime(user.created_at) }}
                </td>
                <td class="px-6 py-4 whitespace-nowrap">
                  <span
                    class="inline-flex px-2 py-1 text-xs font-semibold rounded-full"
                    :class="user.is_active ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'"
                  >
                    {{ user.is_active ? '活跃' : '禁用' }}
                  </span>
                </td>
                <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                  <div class="flex space-x-2">
                    <button
                      @click="editUser(user)"
                      class="text-primary-600 hover:text-primary-900"
                    >
                      编辑
                    </button>
                    <button
                      v-if="user.id !== authStore.user?.id"
                      @click="deleteUser(user)"
                      class="text-red-600 hover:text-red-900"
                    >
                      删除
                    </button>
                  </div>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 创建/编辑用户模态框 -->
    <div v-if="showCreateUser || editingUser" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
        
        <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <form @submit.prevent="saveUser">
            <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
              <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">
                {{ editingUser ? '编辑用户' : '新增用户' }}
              </h3>
              
              <div class="space-y-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700">用户名</label>
                  <input
                    v-model="userForm.username"
                    type="text"
                    required
                    class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700">邮箱</label>
                  <input
                    v-model="userForm.email"
                    type="email"
                    class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  />
                </div>
                
                <div v-if="!editingUser">
                  <label class="block text-sm font-medium text-gray-700">密码</label>
                  <input
                    v-model="userForm.password"
                    type="password"
                    required
                    class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  />
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700">角色</label>
                  <select
                    v-model="userForm.role"
                    class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  >
                    <option value="user">普通用户</option>
                    <option value="admin">管理员</option>
                  </select>
                </div>
                
                <div>
                  <label class="block text-sm font-medium text-gray-700">存储类型</label>
                  <select
                    v-model="userForm.storage_type"
                    class="mt-1 block w-full border-gray-300 rounded-md shadow-sm focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                  >
                    <option value="local">本地存储</option>
                    <option value="webdav">WebDAV</option>
                    <option value="s3">S3</option>
                  </select>
                </div>
              </div>
            </div>
            
            <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
              <button
                type="submit"
                :disabled="isSaving"
                class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-primary-600 text-base font-medium text-white hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
              >
                {{ isSaving ? '保存中...' : '保存' }}
              </button>
              <button
                type="button"
                @click="cancelEdit"
                :disabled="isSaving"
                class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
              >
                取消
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { useAuthStore, useAdminStore } from '@/store'
import { formatDateTime } from '@/utils/helpers'
import {
  UsersIcon,
  PhotoIcon,
  ServerIcon,
  ChartBarIcon,
  PlusIcon
} from '@heroicons/vue/24/outline'

const authStore = useAuthStore()
const adminStore = useAdminStore()

const showCreateUser = ref(false)
const editingUser = ref(null)
const isSaving = ref(false)
const systemStats = ref({})

const userForm = reactive({
  username: '',
  email: '',
  password: '',
  role: 'user',
  storage_type: 'local'
})

// 获取系统统计
const fetchSystemStats = async () => {
  try {
    const stats = await adminStore.fetchSystemStats()
    systemStats.value = stats
  } catch (error) {
    console.error('获取系统统计失败:', error)
  }
}

// 获取用户列表
const fetchUsers = async () => {
  try {
    await adminStore.fetchUsers()
  } catch (error) {
    window.$notify('error', '获取用户列表失败', error.message)
  }
}

// 编辑用户
const editUser = (user) => {
  editingUser.value = user
  userForm.username = user.username
  userForm.email = user.email || ''
  userForm.role = user.role
  userForm.storage_type = user.storage_type || 'local'
}

// 保存用户
const saveUser = async () => {
  try {
    isSaving.value = true
    
    if (editingUser.value) {
      // 更新用户
      await adminStore.updateUser(editingUser.value.id, {
        username: userForm.username,
        email: userForm.email,
        role: userForm.role,
        storage_type: userForm.storage_type
      })
      window.$notify('success', '更新成功', '用户信息已更新')
    } else {
      // 创建用户
      await adminStore.createUser({
        username: userForm.username,
        email: userForm.email,
        password: userForm.password,
        role: userForm.role,
        storage_type: userForm.storage_type
      })
      window.$notify('success', '创建成功', '用户已创建')
    }
    
    cancelEdit()
  } catch (error) {
    window.$notify('error', '保存失败', error.response?.data?.detail || error.message)
  } finally {
    isSaving.value = false
  }
}

// 取消编辑
const cancelEdit = () => {
  showCreateUser.value = false
  editingUser.value = null
  Object.assign(userForm, {
    username: '',
    email: '',
    password: '',
    role: 'user',
    storage_type: 'local'
  })
}

// 删除用户
const deleteUser = async (user) => {
  if (!confirm(`确定要删除用户 "${user.username}" 吗？`)) return
  
  try {
    await adminStore.deleteUser(user.id)
    window.$notify('success', '删除成功', '用户已删除')
  } catch (error) {
    window.$notify('error', '删除失败', error.response?.data?.detail || error.message)
  }
}

onMounted(() => {
  fetchUsers()
  fetchSystemStats()
})
</script>