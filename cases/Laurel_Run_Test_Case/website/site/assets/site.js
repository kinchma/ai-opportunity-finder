document.addEventListener('DOMContentLoaded', function () {
  const navToggle = document.querySelector('[data-nav-toggle]');
  const mainMenu = document.querySelector('[data-main-menu]');

  if (navToggle && mainMenu) {
    function setMenuOpen(isOpen) {
      navToggle.classList.toggle('is-open', isOpen);
      mainMenu.classList.toggle('is-open', isOpen);
      navToggle.setAttribute('aria-expanded', String(isOpen));
    }

    setMenuOpen(false);
    navToggle.addEventListener('click', function () {
      setMenuOpen(!mainMenu.classList.contains('is-open'));
    });
    document.addEventListener('keydown', function (event) {
      if (event.key === 'Escape' && mainMenu.classList.contains('is-open')) {
        setMenuOpen(false);
        navToggle.focus();
      }
    });
  }

  const dealerForm = document.querySelector('#dealer-search-form');
  const dealerState = document.querySelector('#dealer-state');
  const dealerResults = document.querySelector('#dealer-results');
  const dealerCount = document.querySelector('#dealer-count');

  if (dealerForm && dealerState && dealerResults && dealerCount) {
    let dealers = null;

    function addParagraph(parent, text, className) {
      const paragraph = document.createElement('p');
      if (className) paragraph.className = className;
      paragraph.textContent = text;
      parent.appendChild(paragraph);
    }

    function renderDealers() {
      if (!dealers) return;

      const state = dealerState.value;
      dealerResults.textContent = '';
      addParagraph(
        dealerResults,
        'Dealer names and states are fictional. No real contact details are available.',
        'dealer-disclaimer'
      );

      if (!state) {
        dealerCount.textContent = '0 results shown.';
        addParagraph(dealerResults, 'Choose a state to see fictional dealer listings.');
        return;
      }

      const matches = dealers.filter(function (dealer) {
        return dealer.state === state;
      });
      dealerCount.textContent = matches.length + (matches.length === 1 ? ' fictional dealer found.' : ' fictional dealers found.');

      if (!matches.length) {
        addParagraph(dealerResults, 'No fictional dealers were found for ' + state + '.');
        return;
      }

      matches.forEach(function (dealer) {
        const card = document.createElement('article');
        card.className = 'dealer-card';
        const name = document.createElement('h3');
        name.textContent = dealer.dealer_name;
        card.appendChild(name);
        addParagraph(card, 'State: ' + dealer.state, 'dealer-state');
        addParagraph(card, 'Dealer ID: ' + dealer.dealer_id, 'dealer-id');
        const inquiry = document.createElement('a');
        inquiry.className = 'text-link';
        inquiry.href = '/contact/dealer.html?dealer=' + encodeURIComponent(dealer.dealer_name);
        inquiry.textContent = 'Prepare a simulated inquiry';
        card.appendChild(inquiry);
        dealerResults.appendChild(card);
      });
    }

    function showDealerLoadFailure() {
      // Keep any static fallback already present in the page.
      dealerCount.textContent = 'Dealer results are unavailable.';
      addParagraph(
        dealerResults,
        'Fictional dealer listings could not be loaded. No real contact details are available.',
        'dealer-load-error'
      );
    }

    dealerForm.addEventListener('submit', function (event) {
      event.preventDefault();
      renderDealers();
    });
    dealerState.addEventListener('change', renderDealers);

    if (typeof window.fetch === 'function') {
      window.fetch('/assets/dealers.json')
        .then(function (response) {
          if (!response.ok) throw new Error('Dealer data could not be loaded.');
          return response.json();
        })
        .then(function (data) {
          if (!Array.isArray(data) || !data.every(function (dealer) {
            return dealer && typeof dealer.dealer_id === 'string' &&
              typeof dealer.dealer_name === 'string' && typeof dealer.state === 'string';
          })) {
            throw new Error('Dealer data is not in the expected format.');
          }
          dealers = data;
          renderDealers();
        })
        .catch(showDealerLoadFailure);
    } else {
      showDealerLoadFailure();
    }
  }

  const ownerForm = document.querySelector('#owner-confirm-form');
  const industryInput = document.querySelector('#industry-name');
  const companyInput = document.querySelector('#company-name');
  const questionInput = document.querySelector('#confirmation-question');
  const ownerResult = document.querySelector('#owner-confirm-result');

  if (ownerForm && industryInput && companyInput && questionInput && ownerResult) {
    ownerForm.addEventListener('submit', function (event) {
      event.preventDefault();

      const industry = industryInput.value.trim();
      const company = companyInput.value.trim();
      const question = questionInput.value.trim();
      ownerResult.textContent = '';

      if (!industry || !company) {
        const warning = document.createElement('p');
        warning.textContent = 'Please enter a company name and identified industry to prepare the prompt. No message was sent.';
        ownerResult.appendChild(warning);
        return;
      }

      let prompt = 'Hello,\n\nCould you please confirm whether the identified industry for ' + company + ' is ' + industry + '?';
      if (question) prompt += '\n\n' + question;
      prompt += '\n\nThank you.';

      const status = document.createElement('p');
      status.textContent = 'Prepared for your test. No message was sent.';
      ownerResult.appendChild(status);

      const promptText = document.createElement('pre');
      promptText.className = 'owner-confirm-prompt';
      promptText.textContent = prompt;
      ownerResult.appendChild(promptText);

      const copyStatus = document.createElement('p');
      copyStatus.setAttribute('aria-live', 'polite');

      if (navigator.clipboard && typeof navigator.clipboard.writeText === 'function') {
        const copyButton = document.createElement('button');
        copyButton.type = 'button';
        copyButton.textContent = 'Copy prompt';
        copyButton.addEventListener('click', function () {
          try {
            navigator.clipboard.writeText(prompt).then(function () {
              copyStatus.textContent = 'Prompt copied. No message was sent.';
            }).catch(function () {
              copyStatus.textContent = 'Could not copy automatically. Please select and copy the prompt above.';
            });
          } catch (error) {
            copyStatus.textContent = 'Could not copy automatically. Please select and copy the prompt above.';
          }
        });
        ownerResult.appendChild(copyButton);
        copyStatus.textContent = 'You can also select and copy the prompt above manually.';
      } else {
        copyStatus.textContent = 'Select and copy the prompt above manually.';
      }
      ownerResult.appendChild(copyStatus);
    });
  }

  const inquiryForm = document.querySelector('#dealer-inquiry-form');
  const inquiryDealer = document.querySelector('#inquiry-dealer');
  const inquiryModel = document.querySelector('#inquiry-model');
  const inquiryQuestion = document.querySelector('#inquiry-question');
  const inquiryResult = document.querySelector('#dealer-inquiry-result');
  if (inquiryForm && inquiryDealer && inquiryModel && inquiryQuestion && inquiryResult) {
    const namedDealer = new URLSearchParams(window.location.search).get('dealer');
    if (namedDealer) inquiryDealer.value = namedDealer.slice(0, 150);
    inquiryForm.addEventListener('submit', function (event) {
      event.preventDefault();
      const dealer = inquiryDealer.value.trim() || 'Dealer';
      const model = inquiryModel.value.trim();
      const question = inquiryQuestion.value.trim();
      const prompt = 'Hello ' + dealer + ',\n\nI am interested in ' +
        (model || 'a Laurel Run trailer') + '.\n\n' +
        (question || 'Could you tell me about available configurations?') + '\n\nThank you.';
      inquiryResult.textContent = '';
      const status = document.createElement('p');
      status.textContent = 'Prepared for your test. No message was sent.';
      const text = document.createElement('pre');
      text.className = 'owner-confirm-prompt';
      text.textContent = prompt;
      inquiryResult.appendChild(status);
      inquiryResult.appendChild(text);
      const instruction = document.createElement('p');
      instruction.textContent = 'Select and copy the draft above if needed.';
      inquiryResult.appendChild(instruction);
    });
  }
});
