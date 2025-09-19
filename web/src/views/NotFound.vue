<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full text-center">
      <div class="mb-8">
        <h1 class="text-9xl font-bold text-primary-600">404</h1>
        <h2 class="mt-4 text-3xl font-bold text-gray-900">页面未找到</h2>
        <p class="mt-2 text-lg text-gray-600">抱歉，您访问的页面不存在。</p>
      </div>
      
      <div class="space-y-4">
        <router-link
          to="/dashboard"
          class="inline-flex items-center px-4 py-2 border border-transparent text-base font-medium rounded-md text-white bg-primary-600 hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          返回首页
        </router-link>
        
        <button
          @click="$router.go(-1)"
          class="ml-4 inline-flex items-center px-4 py-2 border border-gray-300 text-base font-medium rounded-md text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
        >
          返回上页
        </button>
      </div>
    </div>
  </div>
</template>