window.addEventListener('load', () => {
    /**
     * @type {HTMLButtonElement}
     */
    const loginButton = document.querySelector('*[data-vbox-login-button]');

    /**
     * @type {HTMLFormElement}
     */
    const loginFormElement = document.querySelector('form[data-vbox-login-form]')

    /**
     * @type {HTMLInputElement}
     */
    const passwordInputElement = document.querySelector('input[data-vbox-password-input]');

    /**
     * @type {HTMLInputElement}
     */
    const emailInputElement = document.querySelector('input[data-vbox-email-input]');

    /**
     * @type {HTMLParagraphElement}
     */
    const invalidLoginElement = document.querySelector('p[data-vbox-invalid-login]');

    passwordInputElement.addEventListener('change', () => {
        passwordInputElement.classList.remove('is-invalid');
    });

    emailInputElement.addEventListener('change', () => {
        emailInputElement.classList.remove('is-invalid');
    });

    loginButton.addEventListener('click', (event) => {
        event.stopImmediatePropagation();
        event.preventDefault();

        if (!loginFormElement.checkValidity()) {
            loginFormElement.reportValidity();
        } else {
            const formData = new FormData();
            formData.append('email', emailInputElement.value);
            formData.append('password', passwordInputElement.value);

            invalidLoginElement.classList.add('hidden');

            fetch('/api/login', {
                method: 'POST',
                body: formData
            }).then((response) => {
                if (response.ok) {
                    window.location.replace('/');
                } else {
                    invalidLoginElement.classList.remove('hidden');
                    emailInputElement.classList.add('is-invalid');
                    passwordInputElement.classList.add('is-invalid');
                }
            });
        }

    });

    console.log(loginButton);
});