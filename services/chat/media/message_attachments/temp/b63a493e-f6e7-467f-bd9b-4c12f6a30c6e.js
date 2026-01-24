import http from 'k6/http';
import { check, sleep } from 'k6';

// Это основная функция, которую будет выполнять каждый виртуальный пользователь
export default function () {
  // 1. Отправляем GET запрос
  const res = http.get('https://test-api.k6.io/public/crocodiles/');

  // 2. Проверяем, что сервер ответил "ОК" (код 200)
  check(res, { 'status was 200': (r) => r.status == 200 });

  // 3. Ждем 1 секунду перед следующим запросом (имитация поведения человека)
  sleep(1);
}