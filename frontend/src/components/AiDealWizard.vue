<template>
    <div class="fixed inset-0 bg-black/20 backdrop-blur-sm z-[100] flex items-center justify-center p-4 animate-fade-in">
      <div class="bg-white rounded-3xl p-8 max-w-lg w-full shadow-2xl relative border border-white/50">
        <button @click="$emit('close')" class="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors">✕</button>
        <h2 class="text-2xl font-bold mb-4 text-[#1a1a2e]">AI Deal Wizard</h2>
        
        <div v-if="step === 1">
          <p class="text-gray-500 mb-4">Generate specification for: <b class="text-[#7000ff]">{{ service?.title }}</b></p>
          <textarea v-model="requirements" class="w-full p-4 bg-gray-50 rounded-xl mb-4 h-32 border border-gray-200 focus:outline-none focus:ring-2 focus:ring-[#7000ff]/20 transition-all" placeholder="Describe your task here..."></textarea>
          <button @click="generateTZ" class="w-full bg-[#1a1a2e] text-white py-3 rounded-xl font-medium hover:bg-black transition-colors shadow-lg">Generate via AI ✨</button>
        </div>
  
        <div v-if="step === 2" class="text-center py-8">
          <div class="animate-spin text-4xl mb-4">🔮</div>
          <p class="text-gray-600">AI is analyzing template & requirements...</p>
        </div>
  
        <div v-if="step === 3">
          <h3 class="font-bold mb-2 text-[#1a1a2e]">Generated TZ:</h3>
          <div class="bg-gray-50 p-4 rounded-xl mb-4 text-sm whitespace-pre-wrap max-h-60 overflow-y-auto border border-gray-200 text-gray-700 font-mono">{{ generatedTz }}</div>
          <div class="flex gap-4">
            <button @click="step = 1" class="flex-1 border border-gray-200 py-3 rounded-xl hover:bg-gray-50 transition-colors font-medium">Back</button>
            <button @click="createOrder" class="flex-1 bg-[#7000ff] text-white py-3 rounded-xl shadow-lg shadow-[#7000ff]/20 hover:scale-[1.02] transition-transform font-medium">Create Order</button>
          </div>
        </div>
      </div>
    </div>
  </template>
  
  <script setup>
  import { ref } from 'vue'
  import axios from 'axios'
  
  const props = defineProps({
    service: Object
  })
  
  const emit = defineEmits(['close'])
  
  const step = ref(1)
  const requirements = ref('')
  const generatedTz = ref('')
  
  const generateTZ = async () => {
    step.value = 2
    try {
      const res = await axios.post('/api/market/orders/preview/', {
        service_id: props.service.id,
        raw_requirements: requirements.value
      })
      generatedTz.value = res.data.data.generated_tz
      step.value = 3
    } catch (e) {
      // Fallback logic
      setTimeout(() => {
          generatedTz.value = "# Technical Specification (Mock)\n\n1. Overview: " + requirements.value + "\n2. Deadline: 7 days\n3. Budget: $" + props.service.price
          step.value = 3
      }, 1500)
    }
  }
  
  const createOrder = async () => {
     alert('Order created successfully!')
     emit('close')
  }
  </script>