window.addEventListener('load', () => {
    /**
     * @type {HTMLButtonElement}
     */
    const addNewMappingButton = document.querySelector('button[data-vbox-add-mapping]');
    /**
     * @type {HTMLDivElement}
     */
    const volumeMappingsHolder = document.querySelector('div[data-vbox-volume-mappings]');

    /**
     * @type {HTMLDivElement}
     */
    const volumeMappingError = document.querySelector('div[data-vbox-volume-error]');

    /**
    * @type {HTMLDivElement}
    */
    const configAddError = document.querySelector('div[data-vbox-add-config-error]');

    /**
     * @type {HTMLButtonElement}
     */
    const submitNewConfigurationButton = document.querySelector('button[data-vbox-submit-configuration]');

    /**
     * @type {HTMLFormElement}
     */
    const newConfigurationFormElement = document.querySelector('form[data-vbox-new-configuration-form]');

    /**
     * @type {HTMLTemplateElement}
     */
    const volumeMappingEntryTemplate = document.querySelector('template[data-vbox-mapping-template]');

    class VolumeMappingElement extends HTMLElement {
        constructor() {
            super();

            this.attachShadow({ mode: 'open' })
                .appendChild(volumeMappingEntryTemplate.content.cloneNode(true));
        }

        /**
         * @returns {String}
         */
        get source() {
            /**
          * @type {HTMLInputElement}
          */
            const sourceInput = this.shadowRoot.querySelector('input[data-vbox-source]');

            return sourceInput.value;
        }

        /**
         * @returns {String}
         */
        get destination() {
            /**
          * @type {HTMLInputElement}
          */
            const destInput = this.shadowRoot.querySelector('input[data-vbox-dest]');

            return destInput.value;
        }

        /**
         * @returns {HTMLButtonElement}
         */
        get deleteMappingButton() {
            return this.shadowRoot.querySelector('button[data-vbox-delete-mapping]');
        }
    }

    window.customElements.define(
        'vbox-mapping',
        VolumeMappingElement
    );

    /**
     * @argument {VolumeMappingElement} volumeMappingElement
     * @returns {boolean}
     */
    function isCompleteMapping(volumeMappingElement) {
        return volumeMappingElement.source && volumeMappingElement.destination;
    }

    addNewMappingButton.addEventListener('click', (event) => {
        event.preventDefault();
        event.stopImmediatePropagation();

        volumeMappingError.innerHTML = '';
        volumeMappingError.classList.add('hidden');

        const currentMappings = [...volumeMappingsHolder.querySelectorAll('vbox-mapping')];

        if (currentMappings.map(isCompleteMapping).every(x => x)) {
            const newMappingElement = new VolumeMappingElement();

            newMappingElement.deleteMappingButton.addEventListener('click', () => {
                volumeMappingsHolder.removeChild(newMappingElement);
            });

            volumeMappingsHolder.appendChild(newMappingElement);
        } else {
            volumeMappingError.classList.remove('hidden');
            volumeMappingError.innerHTML = 'Existing mappings are incomplete. Complete them to add a new one.'
        }
    });

    submitNewConfigurationButton.addEventListener('click', async (event) => {
        event.preventDefault();
        event.stopImmediatePropagation();

        if (!newConfigurationFormElement.checkValidity()) {
            newConfigurationFormElement.reportValidity();
        } else {
            /**
             * @type {String}
             */
            const repositoryUrl = newConfigurationFormElement.querySelector('input[data-vbox-repository-url]').value;

            /**
             * @type {String}
             */
            const privateKey = newConfigurationFormElement.querySelector('textarea[data-vbox-private-key]').value;

            const currentMappings = [...volumeMappingsHolder.querySelectorAll('vbox-mapping')].filter(isCompleteMapping).map(volumeMappingElement => {
                return {
                    source: volumeMappingElement.source,
                    destination: volumeMappingElement.destination
                }
            });

            submitNewConfigurationButton.setAttribute('disabled', '');
            addNewMappingButton.setAttribute('disabled', '');

            configAddError.classList.add('hidden');

            await fetch('/api/configuration', {
                method: 'POST',
                credentials: 'include',
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    repositoryUrl,
                    privateKey,
                    currentMappings
                })
            }).then(async (response) => {
                submitNewConfigurationButton.removeAttribute('disabled');
                addNewMappingButton.removeAttribute('disabled');
                if (!response.ok) {
                    const responseContent = await response.json();
                    configAddError.classList.remove('hidden');
                    configAddError.innerHTML = 'Error adding configuration: ' + responseContent.error;
                } else {
                    window.location.reload();
                }
            }).catch(err => {
                addNewMappingButton.removeAttribute('disabled');
                submitNewConfigurationButton.removeAttribute('disabled');
                configAddError.classList.remove('hidden');
                configAddError.innerHTML = 'Error adding configuration: ' + err;
            });
        }
    });

    [...document.querySelectorAll('button[data-vbox-delete-configuration]')].forEach((button) => {
        button.addEventListener('click', () => {
            const id = button.getAttribute('data-vbox-id');

            fetch(`/api/configuration/${id}`, {
                method: 'DELETE',
                credentials: 'include',
                headers: {
                    "Content-Type": "application/json"
                }
            }).then(() => window.location.reload());
        });
    });

    [...document.querySelectorAll('button[data-vbox-pull]')].forEach((button) => {
        const id = button.getAttribute('data-vbox-id');
        button.addEventListener('click', () => {
            button.setAttribute('disabled', '')
            fetch(`/api/configuration/${id}/update`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    "Content-Type": "application/json"
                }
            }).then(() => {
                button.removeAttribute('disabled');
            });
        })
    });

    [...document.querySelectorAll('button[data-vbox-run-build]')].forEach((button) => {
        const id = button.getAttribute('data-vbox-id');
        button.addEventListener('click', () => {
            button.setAttribute('disabled', '')
            fetch(`/api/configuration/${id}/build`, {
                method: 'POST',
                credentials: 'include',
                headers: {
                    "Content-Type": "application/json"
                }
            }).then(() => {
                button.removeAttribute('disabled');
            });
        })
    });
});