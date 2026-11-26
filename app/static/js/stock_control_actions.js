let stockControlActionId = null;
let stockControlActionType = null;

function stockControlActions(row) {
    const id = Number(row.id);
    if (row.type_discount === 'Estat del recipient (Obert / Tancat)' || row.type_discount === 'Obrir tancar') {
        const action = row.is_open ? 'close' : 'open';
        const label = row.is_open ? 'Tancar' : 'Obrir';
        const style = row.is_open ? 'btn-outline-danger' : 'btn-outline-success';
        const icon = row.is_open ? 'fa-lock' : 'fa-box-open';
        return `<button type="button" class="btn ${style} btn-sm" data-stock-action="${action}" data-stock-id="${id}"><i class="fa-solid ${icon}"></i> ${label}</button> ` +
            `<button type="button" class="btn btn-outline-primary btn-sm" data-stock-action="history" data-stock-id="${id}"><i class="fa-solid fa-book"></i> Registres</button>`;
    }
    if (row.type_discount === 'Descompte per reaccions' || row.type_discount === 'Descontar') {
        return `<button type="button" class="btn btn-outline-success btn-sm" data-stock-action="discount" data-stock-id="${id}"><i class="fa-solid fa-vial"></i> Descomptar</button> ` +
            `<button type="button" class="btn btn-outline-primary btn-sm" data-stock-action="history" data-stock-id="${id}"><i class="fa-solid fa-book"></i> Registres</button>`;
    }
    return '';
}

function stockControlToday() {
    const today = new Date();
    return `${String(today.getDate()).padStart(2, '0')}-${String(today.getMonth() + 1).padStart(2, '0')}-${today.getFullYear()}`;
}

function stockControlModalError(id, message) {
    const target = document.getElementById(id);
    target.textContent = message;
    target.hidden = !message;
}

function openStockControlAction(id, action) {
    const row = stockControlRows.find(item => Number(item.id) === id);
    if (!row) return;
    stockControlActionId = id;
    stockControlActionType = action;

    if (action === 'open' || action === 'close') {
        stockControlModalError('stock_control_open_close_error', '');
        document.getElementById('stockControlOpenCloseTitle').textContent = action === 'open' ? 'Obrir lot' : 'Tancar lot';
        document.getElementById('stockControlOpenCloseIcon').className = action === 'open' ? 'fa-solid fa-box-open' : 'fa-solid fa-lock';
        const submitButton = document.getElementById('stock_control_open_close_submit');
        submitButton.className = action === 'open' ? 'btn btn-success btn-sm' : 'btn btn-danger btn-sm';
        submitButton.querySelector('i').className = action === 'open' ? 'fa-solid fa-box-open' : 'fa-solid fa-lock';
        document.getElementById('stock_control_open_close_submit_label').textContent = action === 'open' ? 'Obrir' : 'Tancar';
        document.getElementById('stock_control_open_close_date').value = stockControlToday();
        document.getElementById('stock_control_open_close_observations').value = '';
        $('#stock_control_open_close_modal').modal('show');
    } else if (action === 'discount') {
        stockControlModalError('stock_control_discount_error', '');
        const before = document.getElementById('stock_control_quantity_before');
        const unit = document.getElementById('stock_control_volume_unit');
        before.value = row.quantity_remaining === null ? '' : row.quantity_remaining;
        before.readOnly = row.quantity_remaining !== null;
        unit.value = row.volume_unit || '';
        unit.readOnly = row.quantity_remaining !== null;
        document.getElementById('stock_control_quantity_discounted').value = '';
        document.getElementById('stock_control_discount_date').value = stockControlToday();
        document.getElementById('stock_control_discount_observations').value = '';
        $('#stock_control_discount_modal').modal('show');
    } else if (action === 'history') {
        openStockControlHistory(id);
    }
}

async function saveStockControlOpenClose() {
    const submitButton = document.getElementById('stock_control_open_close_submit');
    submitButton.disabled = true;
    const body = new FormData();
    body.append('id_lot', stockControlActionId);
    body.append('action', stockControlActionType);
    body.append('date_open_close', document.getElementById('stock_control_open_close_date').value.trim());
    body.append('observations', document.getElementById('stock_control_open_close_observations').value.trim());
    try {
        const response = await fetch('/open_close_lots', { method: 'POST', body });
        const result = await response.text();
        if (!response.ok || !result.startsWith('True_')) {
            throw new Error(result.startsWith('False_') ? result.slice(6).split('_')[0] : "No s'ha pogut registrar l'operació.");
        }
        $('#stock_control_open_close_modal').modal('hide');
        await openStockControlPage();
        showModalMessage(stockControlActionType === 'open' ? 'Lot obert correctament.' : 'Lot tancat correctament.', 'success', 'stock_control_message');
    } catch (error) {
        stockControlModalError('stock_control_open_close_error', error.message);
    } finally {
        submitButton.disabled = false;
    }
}

async function saveStockControlDiscount() {
    const submitButton = document.querySelector('#stock_control_discount_form [type="submit"]');
    submitButton.disabled = true;
    const body = new FormData();
    body.append('stock_id', stockControlActionId);
    body.append('quantity_before', document.getElementById('stock_control_quantity_before').value);
    body.append('quantity_discounted', document.getElementById('stock_control_quantity_discounted').value);
    body.append('unit', document.getElementById('stock_control_volume_unit').value.trim());
    body.append('date', document.getElementById('stock_control_discount_date').value.trim());
    body.append('observations', document.getElementById('stock_control_discount_observations').value.trim());
    try {
        const response = await fetch('/stock_control_discount', { method: 'POST', body });
        const data = await response.json();
        if (!response.ok) throw new Error(data.message || "No s'ha pogut registrar el descompte.");
        $('#stock_control_discount_modal').modal('hide');
        await openStockControlPage();
        showModalMessage(`Descompte registrat. Queden ${data.remaining} ${data.unit}.`, 'success', 'stock_control_message');
    } catch (error) {
        stockControlModalError('stock_control_discount_error', error.message);
    } finally {
        submitButton.disabled = false;
    }
}

async function openStockControlHistory(id) {
    try {
        const response = await fetch(`/stock_control_history/${id}`);
        const data = await response.json();
        if (!response.ok) throw new Error(data.message || "No s'han pogut carregar els registres.");
        if (!data.rows.length) {
            showModalMessage('No hi ha registres.', 'warning', 'stock_control_message', 5000);
            return;
        }
        const table = document.getElementById('stock_control_history_table');
        const headers = data.method === 'discount'
            ? ['Data', 'Quantitat anterior', 'Descomptada', 'Restant', 'Unitat', 'Observacions', 'Usuari']
            : ['Data obertura', 'Usuari', 'Observacions obertura', 'Data tancament', 'Usuari', 'Observacions tancament'];
        const fields = data.method === 'discount'
            ? ['date', 'quantity_before', 'quantity_discounted', 'quantity_remaining', 'unit', 'observations', 'user']
            : ['date_open', 'user_open', 'observations_open', 'date_close', 'user_close', 'observations_close'];
        const head = table.tHead || table.createTHead();
        const body = table.tBodies[0] || table.createTBody();
        head.replaceChildren();
        body.replaceChildren();
        const headerRow = head.insertRow();
        headers.forEach(label => {
            const cell = document.createElement('th');
            cell.textContent = label;
            headerRow.appendChild(cell);
        });
        data.rows.forEach(record => {
            const row = body.insertRow();
            fields.forEach(field => { row.insertCell().textContent = record[field] || ''; });
        });
        $('#stock_control_history_modal').modal('show');
    } catch (error) {
        showModalMessage(error.message, 'danger', 'stock_control_message');
    }
}

$(document).ready(function () {
    $('#stock_control_table').on('click', '[data-stock-action]', function () {
        openStockControlAction(Number(this.dataset.stockId), this.dataset.stockAction);
    });
    $('#stock_control_open_close_form').on('submit', function (event) {
        event.preventDefault();
        saveStockControlOpenClose();
    });
    $('#stock_control_discount_form').on('submit', function (event) {
        event.preventDefault();
        saveStockControlDiscount();
    });
});
