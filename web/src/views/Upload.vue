<template>
  <div class="space-y-6">
    <!-- 页面标题 -->
    <div>
      <h1 class="text-2xl font-semibold text-gray-900">上传图片</h1>
      <p class="mt-1 text-sm text-gray-600">选择或拖拽图片文件到下方区域进行上传</p>
    </div>

    <!-- 上传区域 -->
    <div class="bg-white shadow rounded-lg">
      <div class="px-4 py-5 sm:p-6">
        <!-- 拖拽上传区域 -->
        <div
          @drop="handleDrop"
          @dragover="handleDragOver"
          @dragenter="handleDragEnter"
          @dragleave="handleDragLeave"
          class="border-2 border-dashed rounded-lg p-8 text-center transition-colors duration-200"
          :class="[
            isDragging
              ? 'border-primary-500 bg-primary-50'
              : 'border-gray-300 hover:border-gray-400'
          ]"
        >
          <CloudArrowUpIcon class="mx-auto h-12 w-12 text-gray-400" />
          <div class="mt-4">
            <h3 class="text-lg font-medium text-gray-900">上传图片</h3>
            <div class="mt-2">
              <span class="text-sm text-gray-600">拖拽图片到此处，或者</span>
              <label class="cursor-pointer">
                <span class="ml-1 text-primary-600 hover:text-primary-500 font-medium">选择文件</span>
                <input
                  ref="fileInput"
                  type="file"
                  multiple
                  accept="image/*"
                  class="hidden"
                  @change="handleFileSelect"
                />
              </label>
            </div>
            <p class="mt-1 text-xs text-gray-500">
              支持 JPG、PNG、GIF、WebP 格式，单个文件最大 10MB
            </p>
          </div>
        </div>

        <!-- 上传选项 -->
        <div class="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              重命名选项
            </label>
            <select
              v-model="uploadOptions.rename"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            >
              <option value="">保持原名</option>
              <option value="timestamp">时间戳重命名</option>
              <option value="uuid">UUID 重命名</option>
              <option value="random">随机字符串</option>
            </select>
          </div>
          
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">
              上传路径
            </label>
            <input
              v-model="uploadOptions.path"
              type="text"
              placeholder="可选，例如：images/2024/"
              class="block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary-500 focus:border-primary-500 sm:text-sm"
            />
          </div>
        </div>
      </div>
    </div>

    <!-- 上传队列 -->
    <div v-if="Object.keys(fileStore.uploadProgress).length > 0" class="bg-white shadow rounded-lg">
      <div class="px-4 py-5 sm:p-6">
        <h3 class="text-lg leading-6 font-medium text-gray-900 mb-4">上传进度</h3>
        <div class="space-y-4">
          <div
            v-for="(upload, uploadId) in fileStore.uploadProgress"
            :key="uploadId"
            class="border border-gray-200 rounded-lg p-4"
          >
            <div class="flex items-center justify-between mb-2">
              <h4 class="text-sm font-medium text-gray-900">
                上传批次 {{ uploadId }}
              </h4>
              <span
                class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium"
                :class="{
                  'bg-yellow-100 text-yellow-800': upload.status === 'uploading',
                  'bg-green-100 text-green-800': upload.status === 'success',
                  'bg-red-100 text-red-800': upload.status === 'error'
                }"
              >
                {{ upload.status === 'uploading' ? '上传中' : upload.status === 'success' ? '成功' : '失败' }}
              </span>
            </div>
            
            <!-- 总进度条 -->
            <div class="mb-3">
              <div class="flex justify-between text-sm text-gray-600 mb-1">
                <span>总进度</span>
                <span>{{ upload.totalProgress }}%</span>
              </div>
              <div class="w-full bg-gray-200 rounded-full h-2">
                <div
                  class="h-2 rounded-full transition-all duration-300"
                  :class="{
                    'bg-blue-600': upload.status === 'uploading',
                    'bg-green-600': upload.status === 'success',
                    'bg-red-600': upload.status === 'error'
                  }"
                  :style="{ width: upload.totalProgress + '%' }"
                ></div>
              </div>
            </div>

            <!-- 文件列表 -->
            <div class="space-y-2">
              <div
                v-for="file in upload.files"
                :key="file.name"
                class="flex items-center justify-between text-sm"
              >
                <span class="truncate flex-1 pr-4">{{ file.name }}</span>
                <span class="text-gray-500">{{ formatFileSize(file.size) }}</span>
              </div>
            </div>

            <!-- 错误信息 -->
            <div v-if="upload.error" class="mt-3 text-sm text-red-600">
              {{ upload.error }}
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 上传结果 -->
    <div v-if="uploadResults.length > 0" class="bg-white shadow rounded-lg">
      <div class="px-4 py-5 sm:p-6">
        <div class="flex items-center justify-between mb-4">
          <h3 class="text-lg leading-6 font-medium text-gray-900">上传完成</h3>
          <button
            @click="clearResults"
            class="text-sm text-gray-500 hover:text-gray-700"
          >
            清除结果
          </button>
        </div>
        
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="file in uploadResults"
            :key="file.id"
            class="border border-gray-200 rounded-lg p-4"
          >
            <div class="aspect-square rounded-lg overflow-hidden bg-gray-100 mb-3">
              <img
                :src="file.url"
                :alt="file.filename"
                class="h-full w-full object-cover"
                @error="handleImageError"
              />
            </div>
            
            <div class="space-y-2">
              <p class="text-sm font-medium text-gray-900 truncate">{{ file.filename }}</p>
              <p class="text-xs text-gray-500">{{ formatFileSize(file.size) }}</p>
              
              <div class="flex space-x-2">
                <button
                  @click="copyUrl(file.url)"
                  class="flex-1 px-3 py-1 text-xs font-medium text-primary-600 bg-primary-50 rounded hover:bg-primary-100 transition-colors"
                >
                  复制链接
                </button>
                <button
                  @click="previewImage(file)"
                  class="flex-1 px-3 py-1 text-xs font-medium text-gray-600 bg-gray-50 rounded hover:bg-gray-100 transition-colors"
                >
                  预览
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import { useFileStore } from '@/store'
import { formatFileSize, copyToClipboard } from '@/utils/helpers'
import { CloudArrowUpIcon } from '@heroicons/vue/24/outline'

const fileStore = useFileStore()

const fileInput = ref(null)
const isDragging = ref(false)
const uploadResults = ref([])

const uploadOptions = reactive({
  rename: '',
  path: ''
})

// 拖拽事件处理
const handleDragOver = (e) => {
  e.preventDefault()
  e.stopPropagation()
}

const handleDragEnter = (e) => {
  e.preventDefault()
  e.stopPropagation()
  isDragging.value = true
}

const handleDragLeave = (e) => {
  e.preventDefault()
  e.stopPropagation()
  if (e.target === e.currentTarget) {
    isDragging.value = false
  }
}

const handleDrop = (e) => {
  e.preventDefault()
  e.stopPropagation()
  isDragging.value = false

  const files = Array.from(e.dataTransfer.files)
  uploadFiles(files)
}

// 文件选择处理
const handleFileSelect = (e) => {
  const files = Array.from(e.target.files)
  uploadFiles(files)
  // 清空 input，允许重复选择同一文件
  e.target.value = ''
}

// 上传文件
const uploadFiles = async (files) => {
  if (!files || files.length === 0) return

  // 验证文件
  const validFiles = files.filter(file => {
    const isImage = file.type.startsWith('image/')
    const isValidSize = file.size <= 10 * 1024 * 1024 // 10MB
    
    if (!isImage) {
      window.$notify('error', '文件格式错误', `${file.name} 不是有效的图片格式`)
      return false
    }
    
    if (!isValidSize) {
      window.$notify('error', '文件过大', `${file.name} 超过 10MB 限制`)
      return false
    }
    
    return true
  })

  if (validFiles.length === 0) return

  try {
    const result = await fileStore.uploadFiles(validFiles, {
      rename: uploadOptions.rename || undefined,
      path: uploadOptions.path || undefined
    })

    // 添加到上传结果
    if (result.files) {
      uploadResults.value.unshift(...result.files)
    }

    window.$notify('success', '上传成功', `成功上传 ${validFiles.length} 个文件`)
  } catch (error) {
    console.error('上传失败:', error)
    window.$notify('error', '上传失败', error.response?.data?.detail || error.message)
  }
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

// 预览图片
const previewImage = (file) => {
  window.open(file.url, '_blank')
}

// 处理图片加载错误
const handleImageError = (event) => {
  event.target.src = '/placeholder-image.png'
}

// 清除结果
const clearResults = () => {
  uploadResults.value = []
}
</script>