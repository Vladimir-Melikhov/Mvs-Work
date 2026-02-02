// frontend/src/utils/textUtils.js
/**
 * Утилиты для работы с текстом
 */

import DOMPurify from 'dompurify'

/**
 * Удаляет всю markdown-разметку из текста, оставляя только чистый текст
 * @param {string} text - Исходный текст с markdown
 * @returns {string} - Чистый текст без разметки
 */
export function stripMarkdown(text) {
    if (!text) return ''
    
    return text
      // Убираем заголовки (### Header, ## Header, # Header)
      .replace(/^#{1,6}\s+/gm, '')
      
      // Убираем жирный текст (**text** или __text__)
      .replace(/\*\*(.+?)\*\*/g, '$1')
      .replace(/__(.+?)__/g, '$1')
      
      // Убираем курсив (*text* или _text_)
      .replace(/\*(.+?)\*/g, '$1')
      .replace(/_(.+?)_/g, '$1')
      
      // Убираем зачеркнутый текст (~~text~~)
      .replace(/~~(.+?)~~/g, '$1')
      
      // Убираем inline code (`code`)
      .replace(/`(.+?)`/g, '$1')

      .replace(/```[\s\S]*?```/g, '')
      
      .replace(/\[(.+?)\]\(.+?\)/g, '$1')
      
      .replace(/^[\s]*[-*+]\s+/gm, '')
      
      .replace(/^[\s]*\d+\.\s+/gm, '')
      
      .replace(/^[-*_]{3,}$/gm, '')
      
      .replace(/^>\s+/gm, '')
      
      .replace(/\\(.)/g, '$1')

      .replace(/\n{3,}/g, '\n\n')

      .trim()
}

/**
 * Укорачивает текст до заданной длины, добавляя "..." если необходимо
 * @param {string} text - Исходный текст
 * @param {number} maxLength - Максимальная длина
 * @returns {string} - Укороченный текст
 */
export function truncateText(text, maxLength = 100) {
  if (!text) return ''
  if (text.length <= maxLength) return text
  return text.substring(0, maxLength).trim() + '...'
}

/**
 * Проверяет, содержит ли текст markdown-разметку
 * @param {string} text - Проверяемый текст
 * @returns {boolean} - true если содержит разметку
 */
export function hasMarkdown(text) {
  if (!text) return false
  
  const markdownPatterns = [
    /^#{1,6}\s+/m,        // Заголовки
    /\*\*(.+?)\*\*/,      // Жирный текст
    /__(.+?)__/,          // Жирный текст
    /\*(.+?)\*/,          // Курсив
    /_(.+?)_/,            // Курсив
    /~~(.+?)~~/,          // Зачеркнутый
    /`(.+?)`/,            // Inline code
    /```[\s\S]*?```/,     // Блоки кода
    /\[(.+?)\]\(.+?\)/,   // Ссылки
    /^[\s]*[-*+]\s+/m,    // Списки
    /^[\s]*\d+\.\s+/m,    // Нумерованные списки
  ]
  
  return markdownPatterns.some(pattern => pattern.test(text))
}

/**
 * @param {string} html - HTML строка для санитизации
 * @param {boolean} isSystemMessage - Является ли сообщение системным
 * @returns {string} - Санитизированный HTML
 */
export function sanitizeHtml(html, isSystemMessage = false) {
  if (!html) return ''

  const systemMessageConfig = {
    ALLOWED_TAGS: ['span', 'svg', 'path', 'circle', 'g', 'defs', 'linearGradient', 'stop'],
    ALLOWED_ATTR: ['class', 'viewBox', 'fill', 'stroke', 'stroke-width', 'stroke-linecap', 
                   'stroke-linejoin', 'd', 'cx', 'cy', 'r', 'id', 'offset', 'stop-color',
                   'xmlns', 'width', 'height'],
    ALLOW_DATA_ATTR: false,
    ALLOW_UNKNOWN_PROTOCOLS: false,
    SAFE_FOR_TEMPLATES: true
  }
  
  const defaultConfig = {
    ALLOWED_TAGS: [],
    ALLOWED_ATTR: [],
    ALLOW_DATA_ATTR: false,
    ALLOW_UNKNOWN_PROTOCOLS: false,
    SAFE_FOR_TEMPLATES: true
  }
  
  const config = isSystemMessage ? systemMessageConfig : defaultConfig
  
  return DOMPurify.sanitize(html, config)
}

/**
 * @param {string} text - Текст для экранирования
 * @returns {string} - Экранированный текст
 */
export function escapeHtml(text) {
  if (!text) return ''
  
  const div = document.createElement('div')
  div.textContent = text
  return div.innerHTML
}
