<template>
  <svg 
    :class="['system-icon', colorClass]"
    viewBox="0 0 24 24" 
    fill="none" 
    xmlns="http://www.w3.org/2000/svg"
  >
    <component :is="iconPath" />
  </svg>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  type: {
    type: String,
    required: true,
    validator: (value) => [
      'money',
      'ruble',
      'check',
      'work',
      'cancel',
      'warning',
      'clock',
      'lightning',
      'document',
      'info'
    ].includes(value)
  },
  color: {
    type: String,
    default: 'default'
  }
})

const iconPath = computed(() => {
  const icons = {
    money: {
      template: `
        <g>
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
          <path d="M12 6v12M8 9h8M8 15h8" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </g>
      `
    },
    ruble: {
      template: `
        <g>
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
          <path d="M9 7h4.5c1.38 0 2.5 1.12 2.5 2.5S14.88 12 13.5 12H9M9 7v12M7 14h5M9 12h4.5" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </g>
      `
    },
    check: {
      template: `
        <g>
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
          <path d="M8 12l3 3 5-6" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>
        </g>
      `
    },
    work: {
      template: `
        <g>
          <path d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </g>
      `
    },
    cancel: {
      template: `
        <g>
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
          <path d="M15 9l-6 6M9 9l6 6" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </g>
      `
    },
    warning: {
      template: `
        <g>
          <path d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </g>
      `
    },
    clock: {
      template: `
        <g>
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
          <path d="M12 6v6l4 2" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </g>
      `
    },
    lightning: {
      template: `
        <g>
          <path d="M13 2L3 14h8l-1 8 10-12h-8l1-8z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" fill="currentColor"/>
        </g>
      `
    },
    document: {
      template: `
        <g>
          <path d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
        </g>
      `
    },
    info: {
      template: `
        <g>
          <circle cx="12" cy="12" r="10" stroke="currentColor" stroke-width="2"/>
          <path d="M12 16v-4m0-4h.01" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
        </g>
      `
    }
  }
  
  return {
    template: icons[props.type]?.template || icons.info.template
  }
})

const colorClass = computed(() => {
  const colors = {
    success: 'text-green-600',
    error: 'text-red-600',
    warning: 'text-orange-600',
    info: 'text-blue-600',
    purple: 'text-purple-600',
    default: 'text-gray-600'
  }
  return colors[props.color] || colors.default
})
</script>

<style scoped>
.system-icon {
  width: 20px;
  height: 20px;
  flex-shrink: 0;
}
</style>
