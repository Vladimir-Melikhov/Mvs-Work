<template>
    <a 
      :href="telegramLink" 
      target="_blank"
      rel="noopener noreferrer"
      class="support-button"
      title="Служба поддержки"
    >
      <svg 
        class="support-icon" 
        viewBox="0 0 24 24" 
        fill="none" 
        xmlns="http://www.w3.org/2000/svg"
      >
        <path 
          d="M21 11.5a8.38 8.38 0 0 1-.9 3.8 8.5 8.5 0 0 1-7.6 4.7 8.38 8.38 0 0 1-3.8-.9L3 21l1.9-5.7a8.38 8.38 0 0 1-.9-3.8 8.5 8.5 0 0 1 4.7-7.6 8.38 8.38 0 0 1 3.8-.9h.5a8.48 8.48 0 0 1 8 8v.5z" 
          stroke="currentColor" 
          stroke-width="2" 
          stroke-linecap="round" 
          stroke-linejoin="round"
        />
      </svg>
    </a>
  </template>
  
  <script setup>
  import { computed } from 'vue'
  
  const telegramLink = computed(() => {
    const botUsername = import.meta.env.VITE_SUPPORT_BOT_USERNAME || 'your_support_bot'
    return `https://t.me/${botUsername}`
  })
  </script>
  
  <style scoped>
  .support-button {
    position: fixed;
    bottom: 24px;
    right: 24px;
    width: 56px;
    height: 56px;
    background: linear-gradient(135deg, #7000ff 0%, #5500cc 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 4px 12px rgba(112, 0, 255, 0.4);
    transition: all 0.3s ease;
    z-index: 9999;
    cursor: pointer;
  }
  
  .support-button:hover {
    transform: scale(1.1);
    box-shadow: 0 6px 20px rgba(112, 0, 255, 0.6);
  }
  
  .support-button:active {
    transform: scale(0.95);
  }
  
  .support-icon {
    width: 28px;
    height: 28px;
    color: white;
  }

  @media (max-width: 768px) {
    .support-button {
      bottom: 100px;
      right: 16px;
      width: 48px;
      height: 48px;
    }
    
    .support-icon {
      width: 24px;
      height: 24px;
    }
  }
  </style>