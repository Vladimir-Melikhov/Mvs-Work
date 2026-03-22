<!-- frontend/src/views/Error500View.vue -->
<template>
  <div class="error-page">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="grid-overlay"></div>

    <div class="content">
      <div class="error-code-wrap">
        <div class="error-code" data-text="500">500</div>
        <div class="pulse-ring"></div>
      </div>

      <div class="glass-card">
        <div class="icon-wrap">
          <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"/>
          </svg>
        </div>

        <h1 class="title">Что-то пошло не так</h1>
        <p class="desc">
          Сервер споткнулся и упал. Мы уже знаем об этом<br>
          и чиним всё на скорости света. Попробуйте чуть позже.
        </p>

        <!-- Terminal-style error snippet -->
        <div class="terminal">
          <div class="terminal-bar">
            <span class="dot red"></span>
            <span class="dot yellow"></span>
            <span class="dot green"></span>
            <span class="terminal-title">server.log</span>
          </div>
          <div class="terminal-body">
            <div class="log-line"><span class="log-time">{{ time }}</span> <span class="log-level error">ERROR</span> <span class="log-msg">Internal Server Error 500</span></div>
            <div class="log-line"><span class="log-time">{{ time }}</span> <span class="log-level warn">WARN</span> <span class="log-msg">Команда уведомлена</span></div>
            <div class="log-line typing"><span class="log-time">{{ time }}</span> <span class="log-level info">INFO</span> <span class="log-msg">Исправляем...</span><span class="cursor">▌</span></div>
          </div>
        </div>

        <div class="actions">
          <button class="btn-primary" @click="retry">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"/>
            </svg>
            Попробовать снова
          </button>
          <button class="btn-ghost" @click="$router.push('/')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
            </svg>
            На главную
          </button>
        </div>

        <a :href="supportLink" target="_blank" rel="noopener noreferrer" class="support-link">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"/>
          </svg>
          Написать в поддержку
        </a>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()

const time = computed(() => {
  const now = new Date()
  return `${String(now.getHours()).padStart(2,'0')}:${String(now.getMinutes()).padStart(2,'0')}:${String(now.getSeconds()).padStart(2,'0')}`
})

const supportLink = computed(() => {
  const bot = import.meta.env.VITE_SUPPORT_BOT_USERNAME || 'your_support_bot'
  return `https://t.me/${bot}`
})

const retry = () => {
  router.go(-1)
}
</script>

<style scoped>
.error-page {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: #f2f4f8;
  background-image:
    radial-gradient(circle at 20% 20%, rgba(112, 0, 255, 0.2) 0%, transparent 50%),
    radial-gradient(circle at 80% 80%, rgba(0, 198, 255, 0.12) 0%, transparent 50%);
  font-family: 'Outfit', sans-serif;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  pointer-events: none;
}
.orb-1 {
  width: 450px; height: 450px;
  background: rgba(255, 80, 80, 0.08);
  top: -100px; right: -80px;
  animation: float1 9s ease-in-out infinite;
}
.orb-2 {
  width: 300px; height: 300px;
  background: rgba(112, 0, 255, 0.15);
  bottom: -60px; left: -40px;
  animation: float2 7s ease-in-out infinite;
}

@keyframes float1 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-25px,20px)} }
@keyframes float2 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(20px,-25px)} }

.grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(112,0,255,0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(112,0,255,0.04) 1px, transparent 1px);
  background-size: 60px 60px;
  pointer-events: none;
}

.content {
  position: relative;
  display: flex;
  flex-direction: column;
  align-items: center;
  z-index: 1;
  animation: appear 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes appear {
  from { opacity: 0; transform: translateY(30px) scale(0.96); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

.error-code-wrap {
  position: relative;
  margin-bottom: -20px;
  z-index: 2;
}

.error-code {
  font-size: clamp(80px, 18vw, 160px);
  font-weight: 900;
  line-height: 1;
  color: transparent;
  -webkit-text-stroke: 2px rgba(220, 38, 38, 0.35);
  letter-spacing: -4px;
  user-select: none;
  animation: shake 6s ease-in-out infinite;
}

@keyframes shake {
  0%,92%,100% { transform: none; }
  94% { transform: translate(-2px, 1px) rotate(-0.5deg); }
  96% { transform: translate(2px, -1px) rotate(0.5deg); }
  98% { transform: translate(-1px, 0); }
}

.pulse-ring {
  position: absolute;
  inset: 50%;
  transform: translate(-50%, -50%);
  width: 40px; height: 40px;
  border: 2px solid rgba(220, 38, 38, 0.4);
  border-radius: 50%;
  animation: pulse 2s ease-out infinite;
  pointer-events: none;
}

@keyframes pulse {
  0% { width: 40px; height: 40px; opacity: 0.8; }
  100% { width: 200px; height: 200px; opacity: 0; }
}

.glass-card {
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 32px;
  padding: 48px 48px 40px;
  max-width: 500px;
  width: calc(100vw - 32px);
  text-align: center;
  box-shadow:
    0 32px 64px rgba(220, 38, 38, 0.06),
    0 8px 24px rgba(0,0,0,0.06),
    inset 0 1px 0 rgba(255,255,255,0.9);
  position: relative;
  overflow: hidden;
}

.glass-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(220,38,38,0.3), rgba(112,0,255,0.3), transparent);
}

.icon-wrap {
  width: 64px; height: 64px;
  background: linear-gradient(135deg, rgba(220,38,38,0.1), rgba(112,0,255,0.06));
  border: 1px solid rgba(220,38,38,0.2);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}
.icon { width: 32px; height: 32px; color: #dc2626; }

.title {
  font-size: 26px;
  font-weight: 800;
  color: #1a1a2e;
  margin: 0 0 12px;
  letter-spacing: -0.5px;
}

.desc {
  font-size: 15px;
  color: #71717a;
  line-height: 1.7;
  margin: 0 0 24px;
}

/* Terminal */
.terminal {
  background: #0f0f1a;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 28px;
  text-align: left;
  box-shadow: 0 8px 24px rgba(0,0,0,0.15);
}

.terminal-bar {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  background: rgba(255,255,255,0.05);
  border-bottom: 1px solid rgba(255,255,255,0.06);
}

.dot {
  width: 10px; height: 10px;
  border-radius: 50%;
}
.dot.red { background: #ff5f57; }
.dot.yellow { background: #febc2e; }
.dot.green { background: #28c840; }

.terminal-title {
  font-family: 'Outfit', monospace;
  font-size: 11px;
  color: rgba(255,255,255,0.35);
  margin-left: 4px;
}

.terminal-body {
  padding: 14px 16px;
}

.log-line {
  display: flex;
  align-items: center;
  gap: 8px;
  font-family: 'Courier New', monospace;
  font-size: 11px;
  color: rgba(255,255,255,0.6);
  margin-bottom: 6px;
}
.log-line:last-child { margin-bottom: 0; }

.log-time { color: rgba(255,255,255,0.25); }

.log-level {
  padding: 1px 6px;
  border-radius: 4px;
  font-weight: 700;
  font-size: 10px;
  min-width: 36px;
  text-align: center;
}
.log-level.error { background: rgba(220,38,38,0.2); color: #f87171; }
.log-level.warn { background: rgba(245,158,11,0.2); color: #fbbf24; }
.log-level.info { background: rgba(112,0,255,0.2); color: #a78bfa; }

.log-msg { color: rgba(255,255,255,0.5); }

.cursor {
  animation: blink 1s step-end infinite;
  color: #a78bfa;
}
@keyframes blink { 0%,100%{opacity:1} 50%{opacity:0} }

/* Actions */
.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 20px;
}

.btn-primary, .btn-ghost {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 22px;
  border-radius: 14px;
  font-family: 'Outfit', sans-serif;
  font-size: 14px;
  font-weight: 700;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  border: none;
}
.btn-primary svg, .btn-ghost svg { width: 16px; height: 16px; }

.btn-primary {
  background: #1a1a2e;
  color: white;
  box-shadow: 0 8px 24px rgba(26,26,46,0.2);
}
.btn-primary:hover {
  background: #7000ff;
  transform: translateY(-2px);
  box-shadow: 0 12px 28px rgba(112,0,255,0.3);
}

.btn-ghost {
  background: rgba(26,26,46,0.06);
  color: #1a1a2e;
  border: 1px solid rgba(26,26,46,0.1);
}
.btn-ghost:hover {
  background: rgba(26,26,46,0.1);
  transform: translateY(-2px);
}

.support-link {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  color: #7000ff;
  font-weight: 600;
  text-decoration: none;
  transition: opacity 0.2s;
}
.support-link svg { width: 14px; height: 14px; }
.support-link:hover { opacity: 0.7; }

@media (max-width: 480px) {
  .glass-card { padding: 36px 20px 32px; }
  .actions { flex-direction: column; }
  .btn-primary, .btn-ghost { justify-content: center; }
}
</style>