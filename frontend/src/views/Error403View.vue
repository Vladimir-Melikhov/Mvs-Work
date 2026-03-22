<!-- frontend/src/views/Error403View.vue -->
<template>
  <div class="error-page">
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="grid-overlay"></div>

    <!-- Scanlines effect -->
    <div class="scanlines"></div>

    <div class="content">
      <div class="error-code-wrap">
        <div class="error-code" data-text="403">403</div>
        <div class="lock-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"/>
          </svg>
        </div>
      </div>

      <div class="glass-card">
        <div class="access-denied">
          <div class="badge">
            <span class="badge-dot"></span>
            ДОСТУП ЗАПРЕЩЁН
          </div>
        </div>

        <h1 class="title">Закрытая зона</h1>
        <p class="desc">
          У вас нет разрешения на просмотр этой страницы.<br>
          Войдите в аккаунт или вернитесь туда, откуда пришли.
        </p>

        <div class="divider"></div>

        <div class="actions">
          <button class="btn-primary" @click="goLogin">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M11 16l-4-4m0 0l4-4m-4 4h14m-5 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h7a3 3 0 013 3v1"/>
            </svg>
            Войти в аккаунт
          </button>
          <button class="btn-ghost" @click="$router.push('/')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
            </svg>
            На главную
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
const router = useRouter()

const goLogin = () => router.push('/login')
</script>

<style scoped>
.error-page {
  position: fixed;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  background: #0f0f1a;
  font-family: 'Outfit', sans-serif;
}

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  pointer-events: none;
}
.orb-1 {
  width: 500px; height: 500px;
  background: rgba(112, 0, 255, 0.2);
  top: -120px; left: -80px;
  animation: float1 10s ease-in-out infinite;
}
.orb-2 {
  width: 350px; height: 350px;
  background: rgba(112, 0, 255, 0.1);
  bottom: -80px; right: -60px;
  animation: float2 8s ease-in-out infinite;
}

@keyframes float1 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(30px,20px)} }
@keyframes float2 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-20px,-30px)} }

.grid-overlay {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(112,0,255,0.07) 1px, transparent 1px),
    linear-gradient(90deg, rgba(112,0,255,0.07) 1px, transparent 1px);
  background-size: 50px 50px;
  pointer-events: none;
}

.scanlines {
  position: absolute;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,0,0,0.15) 2px,
    rgba(0,0,0,0.15) 4px
  );
  pointer-events: none;
  opacity: 0.4;
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
  display: flex;
  align-items: center;
  justify-content: center;
}

.error-code {
  font-size: clamp(80px, 18vw, 160px);
  font-weight: 900;
  line-height: 1;
  color: transparent;
  -webkit-text-stroke: 2px rgba(112, 0, 255, 0.5);
  letter-spacing: -4px;
  user-select: none;
  filter: drop-shadow(0 0 20px rgba(112,0,255,0.3));
}

.lock-icon {
  position: absolute;
  right: -20px;
  top: 50%;
  transform: translateY(-50%);
  width: 48px; height: 48px;
  background: rgba(112,0,255,0.15);
  border: 1px solid rgba(112,0,255,0.3);
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: lockShake 4s ease-in-out infinite;
  backdrop-filter: blur(8px);
}
.lock-icon svg {
  width: 22px; height: 22px;
  color: #a78bfa;
}

@keyframes lockShake {
  0%,90%,100% { transform: translateY(-50%) rotate(0); }
  92% { transform: translateY(-50%) rotate(-5deg); }
  94% { transform: translateY(-50%) rotate(5deg); }
  96% { transform: translateY(-50%) rotate(-3deg); }
  98% { transform: translateY(-50%) rotate(0); }
}

/* Glass card — dark theme */
.glass-card {
  background: rgba(255, 255, 255, 0.05);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 32px;
  padding: 48px 48px 40px;
  max-width: 460px;
  width: calc(100vw - 32px);
  text-align: center;
  box-shadow:
    0 32px 64px rgba(0,0,0,0.3),
    0 0 0 1px rgba(112,0,255,0.1),
    inset 0 1px 0 rgba(255,255,255,0.08);
  position: relative;
  overflow: hidden;
}

.glass-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(112,0,255,0.5), rgba(167,139,250,0.5), transparent);
}

.access-denied {
  margin-bottom: 20px;
}

.badge {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  background: rgba(220,38,38,0.15);
  border: 1px solid rgba(220,38,38,0.3);
  color: #f87171;
  padding: 5px 14px;
  border-radius: 20px;
  font-size: 11px;
  font-weight: 800;
  letter-spacing: 1.5px;
}

.badge-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #f87171;
  animation: pulse-dot 1.5s ease-in-out infinite;
}

@keyframes pulse-dot {
  0%,100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(0.8); }
}

.title {
  font-size: 26px;
  font-weight: 800;
  color: #f1f1f1;
  margin: 0 0 12px;
  letter-spacing: -0.5px;
}

.desc {
  font-size: 15px;
  color: rgba(255,255,255,0.4);
  line-height: 1.7;
  margin: 0 0 28px;
}

.divider {
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.1), transparent);
  margin-bottom: 28px;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
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
  background: linear-gradient(135deg, #7000ff, #5500cc);
  color: white;
  box-shadow: 0 8px 24px rgba(112,0,255,0.3);
}
.btn-primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 14px 32px rgba(112,0,255,0.4);
}

.btn-ghost {
  background: rgba(255,255,255,0.07);
  color: rgba(255,255,255,0.7);
  border: 1px solid rgba(255,255,255,0.1);
}
.btn-ghost:hover {
  background: rgba(255,255,255,0.12);
  color: white;
  transform: translateY(-2px);
}

@media (max-width: 480px) {
  .glass-card { padding: 36px 20px 32px; }
  .actions { flex-direction: column; }
  .btn-primary, .btn-ghost { justify-content: center; }
  .lock-icon { display: none; }
}
</style>