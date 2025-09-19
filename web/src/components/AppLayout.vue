<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 导航栏 -->
    <nav class="bg-white shadow-lg">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between h-16">
          <!-- Logo 和导航链接 -->
          <div class="flex items-center">
            <div class="flex-shrink-0">
              <h1 class="text-xl font-bold text-primary-600">WPIC 图床</h1>
            </div>
            <div class="hidden md:ml-6 md:flex md:space-x-8">
              <router-link
                v-for="item in navigationItems"
                :key="item.name"
                :to="item.to"
                class="px-3 py-2 rounded-md text-sm font-medium transition-colors duration-200"
                :class="[
                  $route.name === item.name
                    ? 'text-primary-600 bg-primary-50'
                    : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
                ]"
              >
                <component :is="item.icon" class="h-5 w-5 inline-block mr-2" />
                {{ item.label }}
              </router-link>
            </div>
          </div>

          <!-- 用户菜单 -->
          <div class="flex items-center">
            <div class="relative">
              <button
                @click="showUserMenu = !showUserMenu"
                class="flex items-center text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
              >
                <div class="h-8 w-8 rounded-full bg-primary-600 flex items-center justify-center">
                  <span class="text-white font-medium">
                    {{ user?.username?.charAt(0).toUpperCase() || 'U' }}
                  </span>
                </div>
                <span class="ml-2 text-gray-700">{{ user?.username }}</span>
                <ChevronDownIcon class="ml-1 h-4 w-4 text-gray-500" />
              </button>

              <!-- 下拉菜单 -->
              <div
                v-show="showUserMenu"
                @click="showUserMenu = false"
                class="absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-10"
              >
                <div class="px-4 py-2 text-sm text-gray-500 border-b">
                  {{ user?.email || '用户信息' }}
                </div>
                <button
                  @click="handleLogout"
                  class="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                >
                  退出登录
                </button>
              </div>
            </div>
          </div>

          <!-- 移动端菜单按钮 -->
          <div class="md:hidden flex items-center">
            <button
              @click="showMobileMenu = !showMobileMenu"
              class="inline-flex items-center justify-center p-2 rounded-md text-gray-400 hover:text-gray-500 hover:bg-gray-100 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-primary-500"
            >
              <Bars3Icon v-if="!showMobileMenu" class="h-6 w-6" />
              <XMarkIcon v-else class="h-6 w-6" />
            </button>
          </div>
        </div>
      </div>

      <!-- 移动端菜单 -->
      <div v-show="showMobileMenu" class="md:hidden">
        <div class="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-white border-t">
          <router-link
            v-for="item in navigationItems"
            :key="item.name"
            :to="item.to"
            @click="showMobileMenu = false"
            class="block px-3 py-2 rounded-md text-base font-medium transition-colors duration-200"
            :class="[
              $route.name === item.name
                ? 'text-primary-600 bg-primary-50'
                : 'text-gray-500 hover:text-gray-700 hover:bg-gray-100'
            ]"
          >
            <component :is="item.icon" class="h-5 w-5 inline-block mr-2" />
            {{ item.label }}
          </router-link>
        </div>
      </div>
    </nav>

    <!-- 主要内容区域 -->
    <main class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
      <slot />
    </main>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/store'
import {
  HomeIcon,
  CloudArrowUpIcon,
  PhotoIcon,
  Cog6ToothIcon,
  ChevronDownIcon,
  Bars3Icon,
  XMarkIcon
} from '@heroicons/vue/24/outline'

const router = useRouter()
const authStore = useAuthStore()

const showUserMenu = ref(false)
const showMobileMenu = ref(false)

const user = computed(() => authStore.user)

const navigationItems = computed(() => {
  const items = [
    {
      name: 'Dashboard',
      label: '仪表板',
      to: '/dashboard',
      icon: HomeIcon
    },
    {
      name: 'Upload',
      label: '上传图片',
      to: '/upload',
      icon: CloudArrowUpIcon
    },
    {
      name: 'Gallery',
      label: '图片库',
      to: '/gallery',
      icon: PhotoIcon
    }
  ]

  // 只有管理员才能看到设置页面
  if (authStore.isAdmin) {
    items.push({
      name: 'Settings',
      label: '系统设置',
      to: '/settings',
      icon: Cog6ToothIcon
    })
  }

  return items
})

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}

// 点击外部关闭下拉菜单
const handleClickOutside = (event) => {
  if (!event.target.closest('.relative')) {
    showUserMenu.value = false
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>