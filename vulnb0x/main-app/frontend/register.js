window.addEventListener('load', () => {
    /**
     * @type {HTMLButtonElement}
     */
    const registerButton = document.querySelector('*[data-vbox-register-button]');

    /**
     * @type {HTMLFormElement}
     */
    const registerFormElement = document.querySelector('form[data-vbox-register-form]')

    /**
     * @type {HTMLInputElement}
     */
    const passwordInputElement = document.querySelector('input[data-vbox-password-input]');

    /**
     * @type {HTMLInputElement}
     */
    const repeatPasswordInputElement = document.querySelector('input[data-vbox-password-repeat-input]');

    /**
     * @type {HTMLInputElement}
     */
    const emailInputElement = document.querySelector('input[data-vbox-email-input]');

    /**
     * @type {HTMLParagraphElement}
     */
    const invalidRegisterElement = document.querySelector('p[data-vbox-invalid-register]');

    /**
     * @type {HTMLElement}
     */
    const repeatInvalidElement = document.querySelector('small[data-vbox-repeat-invalid]')

    passwordInputElement.addEventListener('change', () => {
        passwordInputElement.classList.remove('is-invalid');
    });

    emailInputElement.addEventListener('change', () => {
        emailInputElement.classList.remove('is-invalid');
    });

    registerButton.addEventListener('click', (event) => {
        event.stopImmediatePropagation();
        event.preventDefault();

        repeatInvalidElement.classList.add('hidden');

        if (!registerFormElement.checkValidity()) {
            registerFormElement.reportValidity();
        } else {

            if (repeatPasswordInputElement.value !== passwordInputElement.value) {
                repeatInvalidElement.classList.remove('hidden');
                repeatPasswordInputElement.classList.add('is-invalid');
                passwordInputElement.classList.add('is-invalid');
            } else {
                const formData = new FormData();
                formData.append('email', emailInputElement.value);
                formData.append('password', passwordInputElement.value);

                invalidRegisterElement.classList.add('hidden');

                fetch('/api/register', {
                    method: 'POST',
                    body: formData
                }).then((response) => {
                    if (response.ok) {
                        window.location.replace('/');
                    } else {
                        invalidRegisterElement.classList.remove('hidden');
                        emailInputElement.classList.add('is-invalid');
                    }
                });
            }
        }
    });
});