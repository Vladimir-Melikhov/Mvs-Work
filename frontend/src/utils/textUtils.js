/**
 * Утилиты для работы с текстом
 */

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
      
      // Убираем блоки кода (```code```)
      .replace(/```[\s\S]*?```/g, '')
      
      // Убираем ссылки [text](url) -> text
      .replace(/\[(.+?)\]\(.+?\)/g, '$1')
      
      // Убираем маркеры списков (-, *, +)
      .replace(/^[\s]*[-*+]\s+/gm, '')
      
      // Убираем нумерованные списки (1. , 2. и т.д.)
      .replace(/^[\s]*\d+\.\s+/gm, '')
      
      // Убираем горизонтальные линии (---, ***, ___)
      .replace(/^[-*_]{3,}$/gm, '')
      
      // Убираем цитаты (> text)
      .replace(/^>\s+/gm, '')
      
      // Убираем escape-символы (\)
      .replace(/\\(.)/g, '$1')
      
      // Убираем лишние пустые строки (оставляем максимум одну)
      .replace(/\n{3,}/g, '\n\n')
      
      // Убираем пробелы в начале и конце
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
