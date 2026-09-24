/**
 * main.js — Основной скрипт сайта «Баш Вояж».
 *
 * Содержит:
 * - Маску ввода телефона
 * - Инициализацию модальных окон бронирования
 * - Живой калькулятор стоимости
 * - Фильтрацию туров
 * - AJAX-отправку формы
 * - Баннер cookie
 * - Инициализацию Cloudflare Turnstile
 */



/* =========================================================================
   1. ГЛОБАЛЬНЫЕ ФУНКЦИИ (Доступны всем обработчикам)
   ========================================================================= */

/**
 * Применяет маску ввода номера телефона формата +7 (XXX) XXX-XX-XX
 */
function applyPhoneMaskDirect(input) {
  let value = input.value.replace(/\D/g, '');
  if (!value) {
    input.value = '';
    return;
  }

  if (value.startsWith('7') || value.startsWith('8')) {
    value = value.substring(1);
  }

  let formatted = '+7';
  if (value.length > 0) formatted += ' (' + value.substring(0, 3);
  if (value.length >= 3) formatted += ') ' + value.substring(3, 6);
  if (value.length >= 6) formatted += '-' + value.substring(6, 8);
  if (value.length >= 8) formatted += '-' + value.substring(8, 10);

  input.value = formatted;
}

// Делегирование событий для всех полей телефона (статических и динамических)
document.addEventListener('input', function(e) {
  const input = e.target.closest('input[type="tel"]');
  if (input) {
    applyPhoneMaskDirect(input);
  }
});

// ======== ОБРАБОТЧИК ДЛЯ ССЫЛКИ "НАСТРОЙКИ COOKIE" (делегирование) ========
document.addEventListener('click', function(e) {
    const settingsLink = e.target.closest('#cookie-settings');
    if (settingsLink) {
        e.preventDefault();
        localStorage.removeItem('cookie_consent');
        location.reload(); // перезагружаем, чтобы баннер появился снова
    }
});

/* =========================================================================
   2. ОСНОВНОЙ ИНИЦИАЛИЗАЦИОННЫЙ БЛОК ПРИ ЗАГРУЗКЕ СТРАНИЦЫ
   ========================================================================= */
document.addEventListener('DOMContentLoaded', function() {

   const consent = localStorage.getItem('cookie_consent');

    if (consent === 'true') {
        // Пользователь согласился – загружаем аналитику и выходим
        loadAnalytics();
        return;
    } else if (consent === 'false') {
        // Пользователь отказался – просто выходим, баннер не показываем
        return;
    }
    // Если согласия нет (null) – показываем баннер (код ниже)

 
  /* ---------------------------------------------------------
     ИНИЦИАЛИЗАЦИЯ МОДАЛЬНЫХ ОКНО (СТРОГО ОДИН РАЗ!)
  --------------------------------------------------------- */
  const step1ModalEl = document.getElementById('bookingStep1Modal');
  const step2ModalEl = document.getElementById('bookingStep2Modal');

  const modalStep1 = step1ModalEl ? new bootstrap.Modal(step1ModalEl) : null;
  const modalStep2 = step2ModalEl ? new bootstrap.Modal(step2ModalEl) : null;

  /* ---------------------------------------------------------
     КНОПКА "НАВЕРХ"
  --------------------------------------------------------- */
  const scrollTopBtn = document.getElementById('scroll-to-top-btn');
  if (scrollTopBtn) {
    window.addEventListener('scroll', () => {
      scrollTopBtn.classList.toggle('d-none', window.scrollY <= 300);
    });
    scrollTopBtn.addEventListener('click', () => {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ---------------------------------------------------------
     КАЛЬКУЛЯТОР СТОИМОСТИ (живой расчёт из data-атрибутов)
  --------------------------------------------------------- */
  const tourSelect = document.getElementById('step1-tour-name');
  const adultsInput = document.getElementById('adults-count');
  const childrenInput = document.getElementById('children-count');

  const priceBox = document.getElementById('live-price-box');
  const baseCostEl = document.getElementById('live-base-cost');
  const discountRow = document.getElementById('live-discount-row');
  const discountAmountEl = document.getElementById('live-discount-amount');
  const totalCostEl = document.getElementById('live-total-cost');

  function calculateLivePrice() {
    if (!tourSelect || tourSelect.selectedIndex === -1) return;

    const selectedOption = tourSelect.options[tourSelect.selectedIndex];
    const adults = adultsInput ? (parseInt(adultsInput.value, 10) || 0) : 0;
    const children = childrenInput ? (parseInt(childrenInput.value, 10) || 0) : 0;
    const totalGuests = adults + children;

    if (!selectedOption || selectedOption.value === "" || totalGuests <= 0) {
      priceBox?.classList.add('d-none');
      discountRow?.classList.add('d-none');
      return;
    }

    const costAdult = parseFloat(selectedOption.getAttribute('data-price-adult')) || 0;
    const costChild = parseFloat(selectedOption.getAttribute('data-price-child')) || costAdult;

    const baseCost = (costAdult * adults) + (costChild * children);
    let finalCost = baseCost;

    if (priceBox) priceBox.classList.remove('d-none');
    if (baseCostEl) baseCostEl.textContent = `${baseCost.toLocaleString('ru-RU')} руб.`;

    if (totalGuests >= 5) {
      const discount = baseCost * 0.10;
      finalCost = baseCost - discount;
      if (discountRow) discountRow.classList.remove('d-none');
      if (discountAmountEl) discountAmountEl.textContent = `-${discount.toLocaleString('ru-RU')} руб.`;
    } else {
      if (discountRow) discountRow.classList.add('d-none');
    }

    if (totalCostEl) totalCostEl.textContent = `${finalCost.toLocaleString('ru-RU')} руб.`;
  }

  if (tourSelect) tourSelect.addEventListener('change', calculateLivePrice);
  if (adultsInput) {
    adultsInput.addEventListener('input', calculateLivePrice);
    adultsInput.addEventListener('change', calculateLivePrice);
  }
  if (childrenInput) {
    childrenInput.addEventListener('input', calculateLivePrice);
    childrenInput.addEventListener('change', calculateLivePrice);
  }

  /* ---------------------------------------------------------
     БЛОКИРОВКА ПРОШЕДШИХ ДАТ
  --------------------------------------------------------- */
  const dateInput = document.getElementById('step1-date');
  if (dateInput) {
    const today = new Date();
    const yyyy = today.getFullYear();
    let mm = today.getMonth() + 1;
    let dd = today.getDate();
    if (mm < 10) mm = '0' + mm;
    if (dd < 10) dd = '0' + dd;
    dateInput.min = `${yyyy}-${mm}-${dd}`;
  }

  /* ---------------------------------------------------------
     ФИЛЬТРЫ ТУРОВ
  --------------------------------------------------------- */
  const filterButtons = document.querySelectorAll('.filter-btn');
  const cards = document.querySelectorAll('.tour-card-item');

  filterButtons.forEach(button => {
    button.addEventListener('click', function() {
        filterButtons.forEach(btn => btn.classList.remove('active'));
        this.classList.add('active');

        const selectedCategory = this.getAttribute('data-category');

        cards.forEach(card => {
            const cardType = card.getAttribute('data-type');
            card.classList.toggle('tour-hidden', !(selectedCategory === 'all' || cardType === selectedCategory));
        });
    });
});
  /* ---------------------------------------------------------
     ОТКРЫТИЕ ШАГА 1 (по клику на кнопки .order-btn)
  --------------------------------------------------------- */
  document.addEventListener('click', function(e) {
    const orderBtn = e.target.closest('.order-btn');

    if (orderBtn && modalStep1) {
      e.preventDefault();
      const tourId = orderBtn.getAttribute('data-tour-id');

      const step1TourIdInput = document.getElementById('step1-tour-id');
      if (step1TourIdInput) step1TourIdInput.value = tourId;

      if (tourSelect) {
        tourSelect.value = tourId;
        calculateLivePrice();
      }

      modalStep1.show();
    }
  });

  document.getElementById('open-booking-step1')?.addEventListener('click', () => {
    if (modalStep1) modalStep1.show();
  });

  /* ---------------------------------------------------------
     ШАГ 1 → ШАГ 2 (валидация и генерация полей участников)
  --------------------------------------------------------- */
  const step1Form = document.getElementById("step1-form-wrapper");

  if (step1Form) {
    step1Form.addEventListener("submit", function (e) {
      e.preventDefault();

      const adults = adultsInput ? (parseInt(adultsInput.value, 10) || 0) : 0;
      const children = childrenInput ? (parseInt(childrenInput.value, 10) || 0) : 0;
      const dateISO = dateInput ? dateInput.value : '';
      const tourId = tourSelect ? tourSelect.value : '';

      if (adults + children < 1) {
        alert("Количество участников должно быть больше 0");
        return;
      }

      const fTourId = document.getElementById("form-tour-id");
      const fDate = document.getElementById("form-date-hidden");
      const fAdults = document.getElementById("form-adults");
      const fChildren = document.getElementById("form-children");
      const fGuests = document.getElementById("form-guests");

      if (fTourId) fTourId.value = tourId;
      if (fDate) fDate.value = dateISO;
      if (fAdults) fAdults.value = adults;
      if (fChildren) fChildren.value = children;
      if (fGuests) fGuests.value = adults + children;

      const wrapper = document.getElementById("participants-wrapper");
      if (wrapper) {
        wrapper.innerHTML = "";

        function addParticipant(type, i) {
          let html = `
            <div class="participant-item mb-3 p-3 bg-light rounded border-0">
              <input type="hidden" name="tourist_is_child" value="${type === 'child' ? '1' : '0'}">
              <h6 class="fw-bold ${type === 'adult' ? 'text-teal-dark' : 'text-orange'}">
                ${type === 'adult' ? 'Взрослый' : 'Ребёнок'} ${i + 1}
              </h6>
              <div class="row g-2">
                <div class="col-4">
                  <label class="form-label small mb-1">Фамилия *</label>
                  <input type="text" name="tourist_last_name" class="form-control form-control-sm" required>
                </div>
                <div class="col-4">
                  <label class="form-label small mb-1">Имя *</label>
                  <input type="text" name="tourist_first_name" class="form-control form-control-sm" required>
                </div>
                <div class="col-4">
  <label class="form-label small mb-1">Отчество </label>
  <input type="text" name="tourist_middle_name"
         class="form-control form-control-sm"
         pattern="[A-Za-zА-Яа-яЁё\s\-]{2,}"
         title="Введите отчество буквами, не менее 2 символов">
  <div class="form-text text-muted mt-1" style="font-size: 0.7rem;">
    <i class="bi bi-info-circle me-1"></i>Если нет отчества — оставьте поле пустым.
  </div>
</div>
              </div>
              <div class="row g-2 mt-2">
                <div class="col-md-4 col-12">
                  <label class="form-label small mb-1">Дата рождения *</label>
                  <input type="date" name="tourist_birthday" class="form-control form-control-sm" required>
                </div>
                ${type === 'adult' ? `
                <div class="col-md-4 col-12">
                  <label class="form-label small mb-1">Телефон *</label>
                  <input type="tel" name="tourist_phone" class="form-control form-control-sm" required>
                </div>
                <div class="col-md-4 col-12">
                  <label class="form-label small mb-1">Email</label>
                  <input type="email" name="tourist_email" class="form-control form-control-sm">
                </div>
                ` : `<div class="col-md-8 col-12"></div>`}
              </div>
            </div>
          `;
          wrapper.insertAdjacentHTML('beforeend', html);
        }

        for (let i = 0; i < adults; i++) addParticipant('adult', i);
        for (let i = 0; i < children; i++) addParticipant('child', i);
      }

      // ---- Переключение модалок с гарантированным закрытием первой ----
      if (modalStep1) {
        if (document.activeElement && step1ModalEl.contains(document.activeElement)) {
          document.activeElement.blur();
        }

        step1ModalEl.addEventListener('hidden.bs.modal', function handler() {
          step1ModalEl.removeEventListener('hidden.bs.modal', handler);

          document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
          document.body.classList.remove('modal-open');
          document.body.style.removeProperty('overflow');
          document.body.style.removeProperty('padding-right');

          // Теперь открываем вторую
          if (modalStep2) {
            modalStep2.show();
          } else {
            alert('Вторая модалка не инициализирована');
          }
        }, { once: true });

        // Закрываем первую модалку
        modalStep1.hide();

        // Страховка: если событие hidden.bs.modal не сработает (например, из-за бага)
        setTimeout(() => {
          // Проверяем, открылась ли вторая модалка
          const isStep2Open = step2ModalEl.classList.contains('show');
          if (!isStep2Open && modalStep2) {
            // Если не открылась, удаляем фоны и открываем принудительно
            document.querySelectorAll('.modal-backdrop').forEach(el => el.remove());
            document.body.classList.remove('modal-open');
            document.body.style.removeProperty('overflow');
            document.body.style.removeProperty('padding-right');
            modalStep2.show();
          }
        }, 500);
      } else {
        // Если первой модалки нет, сразу открываем вторую
        if (modalStep2) modalStep2.show();
      }
    });
  } // <-- ЭТА СКОБКА ЗАКРЫВАЕТ if (step1Form)

  // Логика кнопки "Назад" во втором модальном окне
  document.getElementById('back-to-step-1')?.addEventListener('click', function() {
    if (modalStep2 && modalStep1) {
      modalStep2.hide();
      modalStep1.show();
    }
  });

  /* ---------------------------------------------------------
     ВАЛИДАЦИЯ + AJAX ОТПРАВКА ФОРМЫ В DJANGO
  --------------------------------------------------------- */
  const bookingForm = document.getElementById('booking-form');

  if (bookingForm) {
    bookingForm.addEventListener('submit', async function(e) {
      e.preventDefault();
      e.stopPropagation();

      let isValid = true;

      // Проверка телефонов
      document.querySelectorAll('input[type="tel"]').forEach(input => {
        const phoneRegex = /^\+7\s\([0-9]{3}\)\s[0-9]{3}\-[0-9]{2}\-[0-9]{2}$/;
        input.setCustomValidity('');
        if (!phoneRegex.test(input.value.trim())) {
          input.setCustomValidity('Неверный формат телефона');
          isValid = false;
        }
      });

      // Проверка email
      document.querySelectorAll('input[type="email"]').forEach(input => {
        const emailRegex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        input.setCustomValidity('');
        if (input.value.trim() !== "" && !emailRegex.test(input.value.trim())) {
          input.setCustomValidity('Неверный формат e-mail');
          isValid = false;
        }
      });

      if (!bookingForm.checkValidity() || !isValid) {
        bookingForm.classList.add('was-validated');
        return;
      }

      // CSRF-токен
      const csrfTokenEl = document.querySelector('[name=csrfmiddlewaretoken]');
      const csrfToken = csrfTokenEl ? csrfTokenEl.value : '';

      const formData = new FormData(bookingForm);

      try {
        const response = await fetch("/booking_create/", {
          method: "POST",
          body: formData,
          headers: {
            "X-Requested-With": "XMLHttpRequest",
            "X-CSRFToken": csrfToken
          }
        });

        const data = await response.json();

        if (!data.success) {
          alert(data.error || "Ошибка бронирования");
          return;
        }

        if (modalStep2) modalStep2.hide();

        const successModalElement = document.getElementById('successModal');
        if (successModalElement) {
          new bootstrap.Modal(successModalElement).show();
        }

        bookingForm.reset();
        const wrapper = document.getElementById("participants-wrapper");
        if (wrapper) wrapper.innerHTML = "";
        bookingForm.classList.remove('was-validated');

      } catch (error) {
        alert("Ошибка соединения с сервером");
      }
    });
  }

  /* ---------------------------------------------------------
     ИНИЦИАЛИЗАЦИЯ CLOUDFLARE TURNSTILE
  --------------------------------------------------------- */

  setTimeout(function() {
    if (window.turnstile && window.CF_TURNSTILE_SITE_KEY) {
        turnstile.render('#turnstile-widget', {
            sitekey: window.CF_TURNSTILE_SITE_KEY,
            callback: function(token) { /* ... */ }
        });
    } else {
        console.error("Cloudflare Turnstile не загрузился!");
    }
  }, 500);


    // Создаём баннер
    var banner = document.createElement('div');
    banner.id = 'cookie-banner';
    banner.style.cssText = 'position: fixed; bottom: 0; left: 0; right: 0; background: #2d2d2d; color: #fff; padding: 15px 20px; z-index: 9999; font-family: Arial, sans-serif; box-shadow: 0 -2px 10px rgba(0,0,0,0.3);';

    var container = document.createElement('div');
    container.style.cssText = 'max-width: 1200px; margin: 0 auto; display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 15px;';

    var textDiv = document.createElement('div');
    textDiv.style.cssText = 'flex: 1; min-width: 200px;';
    textDiv.innerHTML = '<span style="font-size: 14px; line-height: 1.5;">Мы используем файлы cookie, чтобы улучшить работу сайта. Вы можете согласиться или отказаться. Подробнее в <a href="' + window.PRIVACY_POLICY_URL + '" style="color: #ffc107; text-decoration: underline;">политике конфиденциальности</a>.</span>';

    var btnDiv = document.createElement('div');
    btnDiv.style.cssText = 'display: flex; gap: 12px; flex-shrink: 0;';

    // Кнопка "Принять"
    var acceptBtn = document.createElement('button');
    acceptBtn.textContent = 'Принять';
    acceptBtn.style.cssText = 'background: #ffc107; color: #000; border: none; padding: 8px 25px; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 14px;';
    acceptBtn.addEventListener('click', function() {
        localStorage.setItem('cookie_consent', 'true');
        loadAnalytics(); // загружаем аналитику только после согласия
        banner.style.display = 'none';
    });

    // Кнопка "Отказаться"
    var rejectBtn = document.createElement('button');
    rejectBtn.textContent = 'Отказаться';
    rejectBtn.style.cssText = 'background: transparent; color: #fff; border: 2px solid #fff; padding: 8px 25px; border-radius: 4px; font-weight: bold; cursor: pointer; font-size: 14px;'; // делаем заметной
    rejectBtn.addEventListener('click', function() {
        localStorage.setItem('cookie_consent', 'false');
        // Аналитику НЕ загружаем
        banner.style.display = 'none';
    });

    btnDiv.appendChild(acceptBtn);
    btnDiv.appendChild(rejectBtn);
    container.appendChild(textDiv);
    container.appendChild(btnDiv);
    banner.appendChild(container);

    // Вставляем баннер в контейнер
    var targetContainer = document.getElementById('cookie-banner-container');
    if (targetContainer) {
        targetContainer.appendChild(banner);
    } else {
        document.body.appendChild(banner);
    }

});


function loadAnalytics() {
    // Здесь счётчики (Яндекс.Метрика, Google Analytics и т.д.)
    console.log('Аналитика загружена (заглушка)');
}