<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div>
      <h1 class="text-2xl font-semibold text-gray-900">仪表板</h1>
      <p class="mt-1 text-sm text-gray-600">欢迎使用 WPIC 图床系统</p>
    </div>

    <!-- 统计卡片 -->
    <div class="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
      <div
        v-for="stat in stats"
        :key="stat.name"
        class="bg-white overflow-hidden shadow rounded-lg"
      >
        <div class="p-5">
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <component :is="stat.icon" class="h-6 w-6 text-gray-400" />
            </div>
            <div class="ml-5 w-0 flex-1">
              <dl>
                <dt class="text-sm font-medium text-gray-500 truncate">{{ stat.name }}</dt>
                <dd>
                  <div class="text-lg font-medium text-gray-900">{{ stat.value }}</div>
                </dd>
              </dl>
            </div>
          </div>
        </div>
        <div class="bg-gray-50 px-5 py-3">
          <div class="text-sm">
            <span
              class="font-medium"
              :class="stat.changeType === 'increase' ? 'text-green-600' : 'text-red-600'"
            >
              {{ stat.change }}
            </span>
            <span class="text-gray-500"> 较上月</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 快速操作 -->
    <div class="bg-white shadow rounded-lg">
      <div class="px-4 py-5 sm:p-6">
        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">快速操作</h3>
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <router-link
            to="/upload"
            class="relative group bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-primary-500 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
          >
            <div>
              <span class="rounded-lg inline-flex p-3 bg-primary-50 text-primary-600 ring-4 ring-white">
                <CloudArrowUpIcon class="h-6 w-6" />
              </span>
            </div>
            <div class="mt-4">
              <h3 class="text-lg font-medium">
                <span class="absolute inset-0" aria-hidden="true"></span>
                上传图片
              </h3>
              <p class="mt-2 text-sm text-gray-500">上传新的图片到图床</p>
            </div>
          </router-link>

          <router-link
            to="/gallery"
            class="relative group bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-primary-500 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
          >
            <div>
              <span class="rounded-lg inline-flex p-3 bg-primary-50 text-primary-600 ring-4 ring-white">
                <PhotoIcon class="h-6 w-6" />
              </span>
            </div>
            <div class="mt-4">
              <h3 class="text-lg font-medium">
                <span class="absolute inset-0" aria-hidden="true"></span>
                图片库
              </h3>
              <p class="mt-2 text-sm text-gray-500">浏览和管理已上传的图片</p>
            </div>
          </router-link>

          <router-link
            v-if="authStore.isAdmin"
            to="/settings"
            class="relative group bg-white p-6 focus-within:ring-2 focus-within:ring-inset focus-within:ring-primary-500 border border-gray-200 rounded-lg hover:shadow-md transition-shadow"
          >
            <div>
              <span class="rounded-lg inline-flex p-3 bg-primary-50 text-primary-600 ring-4 ring-white">
                <Cog6ToothIcon class="h-6 w-6" />
              </span>
            </div>
            <div class="mt-4">
              <h3 class="text-lg font-medium">
                <span class="absolute inset-0" aria-hidden="true"></span>
                系统设置
              </h3>
              <p class="mt-2 text-sm text-gray-500">管理用户和系统配置</p>
            </div>
          </router-link>
        </div>
      </div>
    </div>

    <!-- 最近上传的图片 -->
    <div class="bg-white shadow rounded-lg">
      <div class="px-4 py-5 sm:p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg leading-6 font-medium text-gray-900">最近上传</h3>
          <router-link
            to="/gallery"
            class="text-sm font-medium text-primary-600 hover:text-primary-500"
          >
            查看全部
          </router-link>
        </div>
        
        <div v-if="isLoading" class="flex justify-center py-8">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>

        <div v-else-if="recentFiles.length === 0" class="text-center py-8">
          <PhotoIcon class="mx-auto h-12 w-12 text-gray-400" />
          <h3 class="mt-2 text-sm font-medium text-gray-900">暂无图片</h3>
          <p class="mt-1 text-sm text-gray-500">开始上传您的第一张图片吧</p>
        </div>

        <div v-else class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-6">
          <div
            v-for="file in recentFiles"
            :key="file.id"
            class="relative group cursor-pointer"
            @click="previewImage(file)"
          >
            <div class="aspect-square rounded-lg overflow-hidden bg-gray-100">
              <img
                :src="file.url"
                :alt="file.filename"
                class="h-full w-full object-cover group-hover:opacity-75 transition-opacity"
                @error="handleImageError"
              />
            </div>
            <p class="mt-2 text-xs text-gray-500 truncate">{{ file.filename }}</p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAuthStore, useFileStore } from '@/store'
import { formatFileSize, formatRelativeTime } from '@/utils/helpers'
import {
  PhotoIcon,
  CloudArrowUpIcon,
  Cog6ToothIcon,
  DocumentIcon,
  UsersIcon,
  ServerIcon
} from '@heroicons/vue/24/outline'

const authStore = useAuthStore()
const fileStore = useFileStore()

const isLoading = ref(false)
const recentFiles = ref([])

// 模拟统计数据（实际项目中应该从API获取）
const stats = computed(() => [
  {
    name: '总图片数',
    value: fileStore.totalFiles || 0,
    change: '+12%',
    changeType: 'increase',
    icon: PhotoIcon
  },
  {
    name: '存储使用',
    value: '2.5 GB',
    change: '+8%',
    changeType: 'increase',
    icon: ServerIcon
  },
  {
    name: '今日上传',
    value: '23',
    change: '+5%',
    changeType: 'increase',
    icon: CloudArrowUpIcon
  },
  {
    name: '用户数量',
    value: authStore.isAdmin ? '8' : '1',
    change: '+2%',
    changeType: 'increase',
    icon: UsersIcon
  }
])

// 获取最近上传的文件
const fetchRecentFiles = async () => {
  try {
    isLoading.value = true
    const result = await fileStore.fetchFiles({
      page: 1,
      size: 6,
      sortBy: 'created_at',
      sortOrder: 'desc'
    })
    recentFiles.value = result.items || []
  } catch (error) {
    console.error('获取最近文件失败:', error)
  } finally {
    isLoading.value = false
  }
}

// 预览图片
const previewImage = (file) => {
  // 这里可以实现图片预览功能
  window.open(file.url, '_blank')
}

// 处理图片加载错误
const handleImageError = (event) => {
  event.target.src = '/placeholder-image.png' // 替换为占位图片
}

onMounted(() => {
  fetchRecentFiles()
})
</script>