<template>
  <div class="space-y-6">
    <!-- 页面头部 -->
    <div class="flex flex-col sm:flex-row sm:items-center sm:justify-between">
      <div>
        <h1 class="text-2xl font-semibold text-gray-900">图片库</h1>
        <p class="mt-1 text-sm text-gray-600">管理和浏览您上传的图片</p>
      </div>
      
      <div class="mt-4 sm:mt-0">
        <router-link
          to="/upload"
          class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          <CloudArrowUpIcon class="h-4 w-4 mr-2" />
          上传图片
        </router-link>
      </div>
    </div>

    <!-- 搜索和筛选 -->
    <div class="bg-white shadow rounded-lg">
      <div class="px-4 py-5 sm:p-6">
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <div class="sm:col-span-2">
            <label class="block text-sm font-medium text-gray-700 mb-1">搜索图片</label>
            <div class="relative">
              <input
                v-model="searchQuery"
                type="text"
                placeholder="输入文件名搜索..."
                class="block w-full pl-10 pr-3 py-2 border border-gray-300 rounded-md leading-5 bg-white placeholder-gray-500 focus:outline-none focus:placeholder-gray-400 focus:ring-1 focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
                @input="debouncedSearch"
              />
              <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                <MagnifyingGlassIcon class="h-5 w-5 text-gray-400" />
              </div>
            </div>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">排序方式</label>
            <select
              v-model="sortBy"
              @change="handleSortChange"
              class="block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            >
              <option value="created_at">上传时间</option>
              <option value="filename">文件名</option>
              <option value="size">文件大小</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-1">排序顺序</label>
            <select
              v-model="sortOrder"
              @change="handleSortChange"
              class="block w-full px-3 py-2 border border-gray-300 bg-white rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            >
              <option value="desc">降序</option>
              <option value="asc">升序</option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- 图片列表 -->
    <div class="bg-white shadow rounded-lg">
      <div class="px-4 py-5 sm:p-6">
        <!-- 批量操作工具栏 -->
        <div v-if="selectedFiles.length > 0" class="mb-4 p-3 bg-primary-50 rounded-lg flex items-center justify-between">
          <span class="text-sm text-primary-700">已选择 {{ selectedFiles.length }} 个文件</span>
          <div class="space-x-2">
            <button
              @click="batchCopyUrls"
              class="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded text-primary-700 bg-primary-100 hover:bg-primary-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              批量复制链接
            </button>
            <button
              @click="showDeleteConfirm = true"
              class="inline-flex items-center px-3 py-1 border border-transparent text-sm font-medium rounded text-red-700 bg-red-100 hover:bg-red-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500"
            >
              批量删除
            </button>
          </div>
        </div>

        <!-- 加载状态 -->
        <div v-if="fileStore.isLoading" class="flex justify-center py-12">
          <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        </div>

        <!-- 空状态 -->
        <div v-else-if="fileStore.files.length === 0" class="text-center py-12">
          <PhotoIcon class="mx-auto h-12 w-12 text-gray-400" />
          <h3 class="mt-2 text-sm font-medium text-gray-900">暂无图片</h3>
          <p class="mt-1 text-sm text-gray-500">开始上传您的第一张图片吧</p>
          <div class="mt-6">
            <router-link
              to="/upload"
              class="inline-flex items-center px-4 py-2 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
            >
              <CloudArrowUpIcon class="h-4 w-4 mr-2" />
              上传图片
            </router-link>
          </div>
        </div>

        <!-- 图片网格 -->
        <div v-else class="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-4 xl:grid-cols-6">
          <div
            v-for="file in fileStore.files"
            :key="file.id"
            class="relative group cursor-pointer"
          >
            <!-- 选择框 -->
            <div class="absolute top-2 left-2 z-10">
              <input
                :id="`file-${file.id}`"
                v-model="selectedFiles"
                :value="file.id"
                type="checkbox"
                class="h-4 w-4 text-primary-600 focus:ring-primary-500 border-gray-300 rounded"
              />
            </div>

            <!-- 图片 -->
            <div
              class="aspect-square rounded-lg overflow-hidden bg-gray-100 group-hover:opacity-75 transition-opacity"
              @click="previewImage(file)"
            >
              <img
                :src="file.url"
                :alt="file.filename"
                class="h-full w-full object-cover"
                @error="handleImageError"
              />
            </div>

            <!-- 文件信息 -->
            <div class="mt-2">
              <p class="text-xs font-medium text-gray-900 truncate">{{ file.filename }}</p>
              <p class="text-xs text-gray-500">{{ formatFileSize(file.size) }}</p>
              <p class="text-xs text-gray-500">{{ formatRelativeTime(file.created_at) }}</p>
            </div>

            <!-- 操作按钮 -->
            <div class="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <div class="flex space-x-1">
                <button
                  @click.stop="copyUrl(file.url)"
                  class="p-1 bg-white rounded shadow hover:bg-gray-50"
                  title="复制链接"
                >
                  <DocumentDuplicateIcon class="h-4 w-4 text-gray-600" />
                </button>
                <button
                  @click.stop="deleteFile(file)"
                  class="p-1 bg-white rounded shadow hover:bg-gray-50"
                  title="删除"
                >
                  <TrashIcon class="h-4 w-4 text-red-600" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 分页 -->
        <div v-if="fileStore.pagination.totalPages > 1" class="mt-6 flex items-center justify-between">
          <div class="flex-1 flex justify-between sm:hidden">
            <button
              :disabled="fileStore.pagination.page <= 1"
              @click="changePage(fileStore.pagination.page - 1)"
              class="relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              上一页
            </button>
            <button
              :disabled="fileStore.pagination.page >= fileStore.pagination.totalPages"
              @click="changePage(fileStore.pagination.page + 1)"
              class="ml-3 relative inline-flex items-center px-4 py-2 border border-gray-300 text-sm font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              下一页
            </button>
          </div>
          
          <div class="hidden sm:flex-1 sm:flex sm:items-center sm:justify-between">
            <div>
              <p class="text-sm text-gray-700">
                显示第
                <span class="font-medium">{{ (fileStore.pagination.page - 1) * fileStore.pagination.size + 1 }}</span>
                -
                <span class="font-medium">{{ Math.min(fileStore.pagination.page * fileStore.pagination.size, fileStore.pagination.total) }}</span>
                条，共
                <span class="font-medium">{{ fileStore.pagination.total }}</span>
                条结果
              </p>
            </div>
            <div>
              <nav class="relative z-0 inline-flex rounded-md shadow-sm -space-x-px">
                <button
                  :disabled="fileStore.pagination.page <= 1"
                  @click="changePage(fileStore.pagination.page - 1)"
                  class="relative inline-flex items-center px-2 py-2 rounded-l-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronLeftIcon class="h-5 w-5" />
                </button>
                
                <button
                  v-for="page in visiblePages"
                  :key="page"
                  @click="changePage(page)"
                  class="relative inline-flex items-center px-4 py-2 border text-sm font-medium"
                  :class="[
                    page === fileStore.pagination.page
                      ? 'z-10 bg-primary-50 border-primary-500 text-primary-600'
                      : 'bg-white border-gray-300 text-gray-500 hover:bg-gray-50'
                  ]"
                >
                  {{ page }}
                </button>
                
                <button
                  :disabled="fileStore.pagination.page >= fileStore.pagination.totalPages"
                  @click="changePage(fileStore.pagination.page + 1)"
                  class="relative inline-flex items-center px-2 py-2 rounded-r-md border border-gray-300 bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  <ChevronRightIcon class="h-5 w-5" />
                </button>
              </nav>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 删除确认对话框 -->
    <div v-if="showDeleteConfirm" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-end justify-center min-h-screen pt-4 px-4 pb-20 text-center sm:block sm:p-0">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75 transition-opacity"></div>
        
        <div class="inline-block align-bottom bg-white rounded-lg text-left overflow-hidden shadow-xl transform transition-all sm:my-8 sm:align-middle sm:max-w-lg sm:w-full">
          <div class="bg-white px-4 pt-5 pb-4 sm:p-6 sm:pb-4">
            <div class="sm:flex sm:items-start">
              <div class="mx-auto flex-shrink-0 flex items-center justify-center h-12 w-12 rounded-full bg-red-100 sm:mx-0 sm:h-10 sm:w-10">
                <ExclamationTriangleIcon class="h-6 w-6 text-red-600" />
              </div>
              <div class="mt-3 text-center sm:mt-0 sm:ml-4 sm:text-left">
                <h3 class="text-lg leading-6 font-medium text-gray-900">确认删除</h3>
                <div class="mt-2">
                  <p class="text-sm text-gray-500">
                    您确定要删除选中的 {{ selectedFiles.length }} 个文件吗？此操作无法撤销。
                  </p>
                </div>
              </div>
            </div>
          </div>
          <div class="bg-gray-50 px-4 py-3 sm:px-6 sm:flex sm:flex-row-reverse">
            <button
              @click="confirmDelete"
              :disabled="isDeleting"
              class="w-full inline-flex justify-center rounded-md border border-transparent shadow-sm px-4 py-2 bg-red-600 text-base font-medium text-white hover:bg-red-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-red-500 sm:ml-3 sm:w-auto sm:text-sm disabled:opacity-50"
            >
              {{ isDeleting ? '删除中...' : '确认删除' }}
            </button>
            <button
              @click="showDeleteConfirm = false"
              :disabled="isDeleting"
              class="mt-3 w-full inline-flex justify-center rounded-md border border-gray-300 shadow-sm px-4 py-2 bg-white text-base font-medium text-gray-700 hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500 sm:mt-0 sm:ml-3 sm:w-auto sm:text-sm"
            >
              取消
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useFileStore } from '@/store'
import { formatFileSize, formatRelativeTime, copyToClipboard, debounce } from '@/utils/helpers'
import {
  PhotoIcon,
  CloudArrowUpIcon,
  MagnifyingGlassIcon,
  DocumentDuplicateIcon,
  TrashIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  ExclamationTriangleIcon
} from '@heroicons/vue/24/outline'

const fileStore = useFileStore()

const searchQuery = ref('')
const sortBy = ref('created_at')
const sortOrder = ref('desc')
const selectedFiles = ref([])
const showDeleteConfirm = ref(false)
const isDeleting = ref(false)

// 计算可见的页码
const visiblePages = computed(() => {
  const total = fileStore.pagination.totalPages
  const current = fileStore.pagination.page
  const pages = []
  
  const start = Math.max(1, current - 2)
  const end = Math.min(total, current + 2)
  
  for (let i = start; i <= end; i++) {
    pages.push(i)
  }
  
  return pages
})

// 防抖搜索
const debouncedSearch = debounce(() => {
  handleSearch()
}, 500)

// 处理搜索
const handleSearch = () => {
  fileStore.updateFilters({ search: searchQuery.value })
  fetchFiles()
}

// 处理排序变化
const handleSortChange = () => {
  fileStore.updateFilters({
    sortBy: sortBy.value,
    sortOrder: sortOrder.value
  })
  fetchFiles()
}

// 获取文件列表
const fetchFiles = async () => {
  try {
    await fileStore.fetchFiles()
  } catch (error) {
    window.$notify('error', '获取文件列表失败', error.message)
  }
}

// 切换页面
const changePage = (page) => {
  fileStore.updatePagination({ page })
  fetchFiles()
}

// 预览图片
const previewImage = (file) => {
  window.open(file.url, '_blank')
}

// 复制链接
const copyUrl = async (url) => {
  const success = await copyToClipboard(url)
  if (success) {
    window.$notify('success', '已复制', '图片链接已复制到剪贴板')
  } else {
    window.$notify('error', '复制失败', '无法复制到剪贴板')
  }
}

// 批量复制链接
const batchCopyUrls = async () => {
  const urls = fileStore.files
    .filter(file => selectedFiles.value.includes(file.id))
    .map(file => file.url)
    .join('\n')
  
  const success = await copyToClipboard(urls)
  if (success) {
    window.$notify('success', '已复制', `已复制 ${selectedFiles.value.length} 个图片链接`)
    selectedFiles.value = []
  } else {
    window.$notify('error', '复制失败', '无法复制到剪贴板')
  }
}

// 删除单个文件
const deleteFile = async (file) => {
  if (!confirm(`确定要删除 "${file.filename}" 吗？`)) return
  
  try {
    await fileStore.deleteFile(file.id)
    window.$notify('success', '删除成功', '文件已删除')
  } catch (error) {
    window.$notify('error', '删除失败', error.message)
  }
}

// 确认批量删除
const confirmDelete = async () => {
  try {
    isDeleting.value = true
    await fileStore.deleteFiles(selectedFiles.value)
    window.$notify('success', '删除成功', `已删除 ${selectedFiles.value.length} 个文件`)
    selectedFiles.value = []
    showDeleteConfirm.value = false
  } catch (error) {
    window.$notify('error', '删除失败', error.message)
  } finally {
    isDeleting.value = false
  }
}

// 处理图片加载错误
const handleImageError = (event) => {
  event.target.src = '/placeholder-image.png'
}

onMounted(() => {
  fetchFiles()
})
</script>