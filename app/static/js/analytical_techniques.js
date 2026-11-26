let analyticalTechniquesTable = null;
let editingAnalyticalTechniqueId = null;
let editingAnalyticalTechniqueName = '';
let pendingDeleteAnalyticalTechniqueId = null;

function showAnalyticalTechniqueMessage(message, category = 'success') {
    const target = document.getElementById('analytical_technique_message');
    if (!target) return;
    target.textContent = message;
    target.className = `alert alert-${category}`;
    target.hidden = false;
}

async function analyticalTechniqueRequest(url, body = null) {
    const response = await fetch(url, body ? { method: 'POST', body } : {});
    const data = await response.json();
    if (!response.ok) throw new Error(data.message || 'No s’ha pogut completar l’operació.');
    return data;
}

async function populateAnalyticalTechniqueSelect(selectId, selectedValue = '') {
    const select = document.getElementById(selectId);
    if (!select) return;
    selectedValue = selectedValue && selectedValue !== 'None' ? selectedValue : '';
    try {
        const techniques = await analyticalTechniqueRequest('/analytical_techniques?active=1');
        select.replaceChildren(new Option('Selecciona una tècnica', ''));
        techniques.forEach(technique => select.add(new Option(technique.name, technique.name)));
        if (selectedValue && !techniques.some(technique => technique.name === selectedValue)) {
            select.add(new Option(`${selectedValue} (inactiva)`, selectedValue));
        }
        select.value = selectedValue || '';
    } catch (error) {
        if (selectedValue && !Array.from(select.options).some(option => option.value === selectedValue)) {
            select.add(new Option(selectedValue, selectedValue));
        }
        select.value = selectedValue || '';
        showAnalyticalTechniqueMessage(error.message, 'danger');
    }
}

async function openAnalyticalConfiguration() {
    markSidebarActive('configuration');
    showHomePanel('home-configuration-panel');
    await reloadAnalyticalTechniques();
    if (analyticalTechniquesTable) analyticalTechniquesTable.columns.adjust().draw(false);
}

async function reloadAnalyticalTechniques() {
    if (!analyticalTechniquesTable) return;
    try {
        const rows = await analyticalTechniqueRequest('/analytical_techniques');
        analyticalTechniquesTable.clear().rows.add(rows).draw();
    } catch (error) {
        showAnalyticalTechniqueMessage(error.message, 'danger');
    }
}

function analyticalTechniqueActionButtons(technique) {
    if (editingAnalyticalTechniqueId === technique.id) {
        return `<button type="button" class="btn btn-outline-success btn-sm configuration-action-button" data-technique-action="save" data-technique-id="${technique.id}" title="Guardar"><i class="fa-solid fa-floppy-disk"></i></button> ` +
            `<button type="button" class="btn btn-outline-secondary btn-sm configuration-action-button" data-technique-action="cancel" title="Cancel·lar"><i class="fa-solid fa-xmark"></i></button>`;
    }
    if (!technique.active) {
        return `<button type="button" class="btn btn-outline-success btn-sm configuration-action-button" data-technique-action="restore" data-technique-id="${technique.id}" title="Reactivar"><i class="fa-solid fa-rotate-left"></i></button>`;
    }
    return `<button type="button" class="btn btn-outline-primary btn-sm configuration-action-button" data-technique-action="edit" data-technique-id="${technique.id}" title="Editar"><i class="fa-solid fa-pen"></i></button> ` +
        `<button type="button" class="btn btn-outline-danger btn-sm configuration-action-button" data-technique-action="delete" data-technique-id="${technique.id}" title="Eliminar"><i class="fa-solid fa-trash"></i></button>`;
}

async function saveAnalyticalTechnique(id) {
    const name = editingAnalyticalTechniqueName.trim();
    if (!name) {
        showAnalyticalTechniqueMessage('El nom és obligatori.', 'warning');
        return;
    }
    try {
        await analyticalTechniqueRequest(`/analytical_techniques/${id}`, new URLSearchParams({ name }));
        editingAnalyticalTechniqueId = null;
        await reloadAnalyticalTechniques();
        showAnalyticalTechniqueMessage('Tècnica modificada correctament.');
    } catch (error) {
        showAnalyticalTechniqueMessage(error.message, 'danger');
    }
}

async function setAnalyticalTechniqueActive(id, active) {
    try {
        await analyticalTechniqueRequest(`/analytical_techniques/${id}/active`, new URLSearchParams({ active: active ? '1' : '0' }));
        await reloadAnalyticalTechniques();
        showAnalyticalTechniqueMessage(active ? 'Tècnica reactivada.' : 'Tècnica eliminada.');
    } catch (error) {
        showAnalyticalTechniqueMessage(error.message, 'danger');
    }
}

function confirmDeleteAnalyticalTechnique() {
    if (pendingDeleteAnalyticalTechniqueId === null) return;
    const id = pendingDeleteAnalyticalTechniqueId;
    pendingDeleteAnalyticalTechniqueId = null;
    $('#delete_analytical_technique_modal').modal('hide');
    setAnalyticalTechniqueActive(id, false);
}

$(document).ready(function () {
    if (!document.getElementById('analytical_techniques_table')) return;

    analyticalTechniquesTable = $('#analytical_techniques_table').DataTable({
        data: [],
        dom: 'rtip',
        pageLength: 10,
        autoWidth: false,
        order: [[0, 'asc']],
        columns: [
            {
                data: 'name',
                render: function (name, type, row) {
                    if (type !== 'display') return name;
                    if (editingAnalyticalTechniqueId === row.id) {
                        return '<input type="text" class="form-control form-control-sm analytical-technique-edit" maxlength="100" aria-label="Nom de la tècnica">';
                    }
                    return $.fn.dataTable.render.text().display(name);
                }
            },
            {
                data: 'active',
                render: function (active, type) {
                    if (type !== 'display') return active ? 'Actiu' : 'Inactiu';
                    return active
                        ? '<span class="configuration-status-badge configuration-status-active">Actiu</span>'
                        : '<span class="configuration-status-badge configuration-status-inactive">Inactiu</span>';
                }
            },
            {
                data: null,
                orderable: false,
                searchable: false,
                render: function (_data, type, row) {
                    return type === 'display' ? analyticalTechniqueActionButtons(row) : '';
                }
            }
        ],
        language: {
            emptyTable: 'No hi ha tècniques analítiques',
            zeroRecords: "No s'han trobat tècniques",
            info: 'Mostrant _START_ a _END_ de _TOTAL_ registres',
            infoEmpty: 'Mostrant 0 registres',
            infoFiltered: '(filtrat de _MAX_ registres)',
            paginate: { previous: 'Anterior', next: 'Següent' }
        },
        drawCallback: function () {
            const input = document.querySelector('.analytical-technique-edit');
            if (input) input.value = editingAnalyticalTechniqueName;
        }
    });

    $('#analytical_techniques_search').on('input', function () {
        analyticalTechniquesTable.search(this.value).draw();
    });
    $('#analytical_techniques_length').on('change', function () {
        analyticalTechniquesTable.page.len(Number(this.value)).draw();
    });
    $('#analytical_techniques_clear_filters').on('click', function () {
        $('#analytical_techniques_search').val('');
        analyticalTechniquesTable.search('').order([[0, 'asc']]).draw();
    });
    $('#analytical_techniques_table').on('input', '.analytical-technique-edit', function () {
        editingAnalyticalTechniqueName = this.value;
    });
    $('#analytical_techniques_table').on('click', '[data-technique-action]', function () {
        const action = this.dataset.techniqueAction;
        const id = Number(this.dataset.techniqueId);
        if (action === 'edit') {
            const row = analyticalTechniquesTable.row($(this).closest('tr')).data();
            editingAnalyticalTechniqueId = id;
            editingAnalyticalTechniqueName = row.name;
            analyticalTechniquesTable.rows().invalidate().draw(false);
            document.querySelector('.analytical-technique-edit')?.focus();
        } else if (action === 'cancel') {
            editingAnalyticalTechniqueId = null;
            analyticalTechniquesTable.rows().invalidate().draw(false);
        } else if (action === 'save') {
            saveAnalyticalTechnique(id);
        } else if (action === 'delete') {
            pendingDeleteAnalyticalTechniqueId = id;
            $('#delete_analytical_technique_modal').modal('show');
        } else if (action === 'restore') {
            setAnalyticalTechniqueActive(id, true);
        }
    });
    $('#analytical_technique_form').on('submit', async function (event) {
        event.preventDefault();
        const input = document.getElementById('analytical_technique_name');
        const name = input.value.trim();
        if (!name) return;
        try {
            await analyticalTechniqueRequest('/analytical_techniques', new URLSearchParams({ name }));
            input.value = '';
            await reloadAnalyticalTechniques();
            showAnalyticalTechniqueMessage('Tècnica creada correctament.');
        } catch (error) {
            showAnalyticalTechniqueMessage(error.message, 'danger');
        }
    });
});
