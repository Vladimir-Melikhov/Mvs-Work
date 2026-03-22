<!-- frontend/src/views/Error404View.vue -->
<template>
  <div class="error-page">
    <!-- Floating orbs background -->
    <div class="orb orb-1"></div>
    <div class="orb orb-2"></div>
    <div class="orb orb-3"></div>

    <!-- Grid overlay -->
    <div class="grid-overlay"></div>

    <div class="content">
      <!-- Glitch number -->
      <div class="error-code-wrap">
        <div class="error-code" data-text="404">404</div>
      </div>

      <!-- Glass card -->
      <div class="glass-card">
        <div class="icon-wrap">
          <svg class="icon" viewBox="0 0 24 24" fill="none" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="1.5"
              d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>

        <h1 class="title">Страница не найдена</h1>
        <p class="desc">
          Похоже, эта страница улетела в другую галактику.<br>
          Проверьте адрес или вернитесь на главную.
        </p>

        <div class="actions">
          <button class="btn-primary" @click="$router.push('/')">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"/>
            </svg>
            На главную
          </button>
          <button class="btn-ghost" @click="$router.back()">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10 19l-7-7m0 0l7-7m-7 7h18"/>
            </svg>
            Назад
          </button>
        </div>

        <!-- Hint links -->
        <div class="hints">
          <span class="hint-label">Возможно вы искали:</span>
          <router-link to="/search" class="hint-link">Поиск услуг</router-link>
          <router-link to="/chats" class="hint-link">Чаты</router-link>
          <router-link to="/profile" class="hint-link">Профиль</router-link>
        </div>
      </div>

      <!-- Floating particles -->
      <div class="particles">
        <div v-for="i in 12" :key="i" class="particle" :style="getParticleStyle(i)"></div>
      </div>
    </div>
  </div>
</template>

<script setup>
const getParticleStyle = (i) => {
  const angle = (i / 12) * 360
  const radius = 180 + (i % 3) * 40
  const x = Math.cos((angle * Math.PI) / 180) * radius
  const y = Math.sin((angle * Math.PI) / 180) * radius
  const delay = i * 0.4
  const duration = 3 + (i % 4)
  return {
    '--x': `${x}px`,
    '--y': `${y}px`,
    '--delay': `${delay}s`,
    '--duration': `${duration}s`,
    width: `${4 + (i % 3) * 3}px`,
    height: `${4 + (i % 3) * 3}px`,
    opacity: 0.3 + (i % 4) * 0.1,
  }
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
    radial-gradient(circle at 0% 0%, rgba(112, 0, 255, 0.25) 0%, transparent 60%),
    radial-gradient(circle at 100% 100%, rgba(0, 198, 255, 0.15) 0%, transparent 50%);
  font-family: 'Outfit', sans-serif;
  z-index: 0;
}

/* Orbs */
.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
  pointer-events: none;
}
.orb-1 {
  width: 500px; height: 500px;
  background: rgba(112, 0, 255, 0.18);
  top: -120px; left: -100px;
  animation: float1 8s ease-in-out infinite;
}
.orb-2 {
  width: 350px; height: 350px;
  background: rgba(0, 198, 255, 0.12);
  bottom: -80px; right: -60px;
  animation: float2 10s ease-in-out infinite;
}
.orb-3 {
  width: 250px; height: 250px;
  background: rgba(112, 0, 255, 0.1);
  top: 50%; right: 10%;
  animation: float3 7s ease-in-out infinite;
}

@keyframes float1 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(30px,20px)} }
@keyframes float2 { 0%,100%{transform:translate(0,0)} 50%{transform:translate(-20px,-30px)} }
@keyframes float3 { 0%,100%{transform:translate(0,-50%)} 50%{transform:translate(15px,calc(-50% + 15px))} }

/* Grid overlay */
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
  gap: 0;
  z-index: 1;
  animation: appear 0.7s cubic-bezier(0.16, 1, 0.3, 1);
}

@keyframes appear {
  from { opacity: 0; transform: translateY(30px) scale(0.96); }
  to   { opacity: 1; transform: translateY(0) scale(1); }
}

/* Glitch 404 */
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
  -webkit-text-stroke: 2px rgba(112, 0, 255, 0.4);
  letter-spacing: -4px;
  user-select: none;
  position: relative;
  animation: glitch 4s infinite;
}

.error-code::before,
.error-code::after {
  content: attr(data-text);
  position: absolute;
  inset: 0;
  -webkit-text-stroke: 2px transparent;
}

.error-code::before {
  color: rgba(112, 0, 255, 0.25);
  animation: glitch-before 4s infinite;
  clip-path: polygon(0 0, 100% 0, 100% 40%, 0 40%);
}

.error-code::after {
  color: rgba(0, 198, 255, 0.2);
  animation: glitch-after 4s infinite;
  clip-path: polygon(0 60%, 100% 60%, 100% 100%, 0 100%);
}

@keyframes glitch {
  0%,90%,100% { transform: none; }
  92% { transform: translate(-2px, 1px) skewX(-1deg); }
  94% { transform: translate(2px, -1px) skewX(1deg); }
  96% { transform: translate(-1px, 2px); }
}
@keyframes glitch-before {
  0%,90%,100% { transform: none; opacity:1; }
  92% { transform: translate(3px, -2px); opacity:.8; }
  94% { transform: translate(-3px, 2px); opacity:.8; }
  96% { transform: translate(1px, -1px); opacity:1; }
}
@keyframes glitch-after {
  0%,90%,100% { transform: none; opacity:1; }
  92% { transform: translate(-3px, 1px); opacity:.8; }
  94% { transform: translate(3px, -1px); opacity:.8; }
  96% { transform: translate(-2px, 2px); opacity:1; }
}

/* Glass card */
.glass-card {
  background: rgba(255, 255, 255, 0.65);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.8);
  border-radius: 32px;
  padding: 48px 48px 40px;
  max-width: 480px;
  width: calc(100vw - 32px);
  text-align: center;
  box-shadow:
    0 32px 64px rgba(112, 0, 255, 0.08),
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
  background: linear-gradient(90deg, transparent, rgba(112,0,255,0.3), rgba(0,198,255,0.3), transparent);
}

.icon-wrap {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, rgba(112,0,255,0.12), rgba(0,198,255,0.08));
  border: 1px solid rgba(112,0,255,0.2);
  border-radius: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20px;
}
.icon {
  width: 32px;
  height: 32px;
  color: #7000ff;
}

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
  margin: 0 0 32px;
}

.actions {
  display: flex;
  gap: 12px;
  justify-content: center;
  margin-bottom: 28px;
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
.btn-primary svg, .btn-ghost svg {
  width: 16px; height: 16px;
}

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

.hints {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  justify-content: center;
  font-size: 12px;
}

.hint-label {
  color: #a1a1aa;
  font-weight: 500;
}

.hint-link {
  color: #7000ff;
  font-weight: 700;
  text-decoration: none;
  padding: 3px 10px;
  border-radius: 20px;
  background: rgba(112,0,255,0.06);
  border: 1px solid rgba(112,0,255,0.15);
  transition: all 0.2s;
}
.hint-link:hover {
  background: rgba(112,0,255,0.12);
  transform: translateY(-1px);
}

/* Particles */
.particles {
  position: absolute;
  inset: 0;
  pointer-events: none;
  display: flex;
  align-items: center;
  justify-content: center;
}

.particle {
  position: absolute;
  border-radius: 50%;
  background: linear-gradient(135deg, #7000ff, #00c6ff);
  animation: orbit var(--duration, 4s) ease-in-out infinite var(--delay, 0s) alternate;
}

@keyframes orbit {
  from { transform: translate(calc(var(--x) * 0.7), calc(var(--y) * 0.7)); }
  to   { transform: translate(var(--x), var(--y)); }
}

@media (max-width: 480px) {
  .glass-card { padding: 36px 24px 32px; }
  .actions { flex-direction: column; }
  .btn-primary, .btn-ghost { justify-content: center; }
}
</style>