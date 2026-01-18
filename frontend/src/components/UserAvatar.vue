<template>
    <div 
      :class="containerClass"
      class="rounded-full overflow-hidden flex items-center justify-center shrink-0"
    >
      <img 
        v-if="avatarUrl && !imageError" 
        :src="avatarUrl" 
        :alt="name"
        class="w-full h-full object-cover"
        @error="handleImageError"
      >
      <div 
        v-else 
        class="w-full h-full bg-gradient-to-br from-gray-300 to-gray-400 flex items-center justify-center text-white font-bold"
        :class="initialsClass"
      >
        {{ initials }}
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref, computed } from 'vue'
  
  const props = defineProps({
    avatarUrl: {
      type: String,
      default: null
    },
    name: {
      type: String,
      default: 'User'
    },
    size: {
      type: String,
      default: 'md',
      validator: (value) => ['xs', 'sm', 'md', 'lg', 'xl'].includes(value)
    }
  })
  
  const imageError = ref(false)
  
  const handleImageError = () => {
    imageError.value = true
  }
  
  const containerClass = computed(() => {
    const sizes = {
      xs: 'w-6 h-6',
      sm: 'w-8 h-8',
      md: 'w-10 h-10',
      lg: 'w-12 h-12',
      xl: 'w-16 h-16'
    }
    return sizes[props.size] || sizes.md
  })
  
  const initialsClass = computed(() => {
    const textSizes = {
      xs: 'text-[8px]',
      sm: 'text-[10px]',
      md: 'text-xs',
      lg: 'text-sm',
      xl: 'text-base'
    }
    return textSizes[props.size] || textSizes.md
  })
  
  const initials = computed(() => {
    if (!props.name) return '?'
    const parts = props.name.trim().split(' ')
    if (parts.length >= 2) {
      return (parts[0][0] + parts[1][0]).toUpperCase()
    }
    return props.name.substring(0, 2).toUpperCase()
  })
  </script>
