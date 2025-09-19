<template>
  <div id="app">
    <!-- 如果是登录页或404页，不显示布局 -->
    <template v-if="isLayoutPage">
      <AppLayout>
        <router-view />
      </AppLayout>
    </template>
    
    <!-- 其他页面直接显示内容 -->
    <template v-else>
      <router-view />
    </template>

    <!-- 全局通知组件（可选） -->
    <Teleport to="body">
      <div v-if="notification.show" class="fixed inset-0 z-50 overflow-hidden pointer-events-none">
        <div class="absolute top-4 right-4 max-w-sm w-full pointer-events-auto">
          <div
            class="bg-white rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 p-4"
            :class="{
              'border-l-4 border-green-400': notification.type === 'success',
              'border-l-4 border-red-400': notification.type === 'error',
              'border-l-4 border-yellow-400': notification.type === 'warning',
              'border-l-4 border-blue-400': notification.type === 'info'
            }"
          >
            <div class="flex">
              <div class="flex-shrink-0">
                <CheckCircleIcon v-if="notification.type === 'success'" class="h-5 w-5 text-green-400" />
                <XCircleIcon v-else-if="notification.type === 'error'" class="h-5 w-5 text-red-400" />
                <ExclamationTriangleIcon v-else-if="notification.type === 'warning'" class="h-5 w-5 text-yellow-400" />
                <InformationCircleIcon v-else class="h-5 w-5 text-blue-400" />
              </div>
              <div class="ml-3">
                <p class="text-sm font-medium text-gray-900">{{ notification.title }}</p>
                <p v-if="notification.message" class="mt-1 text-sm text-gray-500">{{ notification.message }}</p>
              </div>
              <div class="ml-auto pl-3">
                <button
                  @click="hideNotification"
                  class="inline-flex rounded-md bg-white text-gray-400 hover:text-gray-500 focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <XMarkIcon class="h-5 w-5" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { computed, reactive, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/store'
import AppLayout from '@/components/AppLayout.vue'
import {
  CheckCircleIcon,
  XCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XMarkIcon
} from '@heroicons/vue/24/outline'

const route = useRoute()
const authStore = useAuthStore()

// 判断是否需要显示布局
const isLayoutPage = computed(() => {
  const noLayoutPages = ['Login', 'NotFound']
  return !noLayoutPages.includes(route.name)
})

// 全局通知状态
const notification = reactive({
  show: false,
  type: 'info', // success, error, warning, info
  title: '',
  message: '',
  timeout: null
})

// 显示通知
const showNotification = (type, title, message = '', duration = 5000) => {
  // 清除之前的定时器
  if (notification.timeout) {
    clearTimeout(notification.timeout)
  }

  notification.type = type
  notification.title = title
  notification.message = message
  notification.show = true

  // 自动隐藏
  if (duration > 0) {
    notification.timeout = setTimeout(() => {
      hideNotification()
    }, duration)
  }
}

// 隐藏通知
const hideNotification = () => {
  notification.show = false
  if (notification.timeout) {
    clearTimeout(notification.timeout)
    notification.timeout = null
  }
}

// 初始化应用
onMounted(async () => {
  // 初始化认证状态
  await authStore.initAuth()
})

// 将通知方法挂载到全局，供其他组件使用
window.$notify = showNotification
</script>

<style>
/* 可以在这里添加全局样式 */
</style>