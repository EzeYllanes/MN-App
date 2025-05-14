// Funciones para la gestión de tipos de financiación
function seleccionarTipo(tipo) {
    // Refrescar columna de tipos con el seleccionado
    fetch(`/configuracion/columna_tipos?tipo=${encodeURIComponent(tipo)}`)
        .then(response => response.text())
        .then(html => {
            document.getElementById('columna-tipos').innerHTML = html;
            // Luego refrescar columna de tarjetas
            fetch(`/configuracion/columna_tarjetas?tipo=${encodeURIComponent(tipo)}`)
                .then(response => response.text())
                .then(html2 => {
                    document.getElementById('columna-tarjetas').innerHTML = html2;
                    // Buscar la primera tarjeta seleccionada en el HTML
                    const tarjetas = document.querySelectorAll('#columna-tarjetas .list-group-item');
                    let tarjeta = null;
                    if (tarjetas.length > 0) {
                        tarjeta = tarjetas[0].querySelector('span').textContent.trim();
                    }
                    if (tarjeta) {
                        fetch(`/configuracion/columna_planes?tipo=${encodeURIComponent(tipo)}&tarjeta=${encodeURIComponent(tarjeta)}`)
                            .then(response => response.text())
                            .then(html3 => {
                                document.getElementById('columna-planes').innerHTML = html3;
                            });
                    } else {
                        document.getElementById('columna-planes').innerHTML = '<h5 id="planes-anchor">Planes</h5><div class="text-muted">Seleccione una tarjeta</div>';
                    }
                });
        });
}

function agregarTipoAjax(form) {
    const formData = new FormData(form);
    fetch('/configuracion/agregar_tipo', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('columna-tipos').innerHTML = data.html;
            document.getElementById('columna-tarjetas').innerHTML = '<h5 id="tarjetas-anchor">Tarjetas</h5><div class="text-muted">Seleccione un tipo</div>';
            document.getElementById('columna-planes').innerHTML = '<h5 id="planes-anchor">Planes</h5><div class="text-muted">Seleccione una tarjeta</div>';
        } else {
            alert(data.error);
        }
    });
    return false;
}

function editarTipoAjax(form) {
    const formData = new FormData(form);
    fetch('/configuracion/editar_tipo', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('columna-tipos').innerHTML = data.html;
            document.getElementById('columna-tarjetas').innerHTML = '<h5 id="tarjetas-anchor">Tarjetas</h5><div class="text-muted">Seleccione un tipo</div>';
            document.getElementById('columna-planes').innerHTML = '<h5 id="planes-anchor">Planes</h5><div class="text-muted">Seleccione una tarjeta</div>';
        } else {
            alert(data.error);
        }
    });
    return false;
}

function eliminarTipoAjax(form) {
    if (!confirm('¿Está seguro de eliminar este tipo de financiación?')) {
        return false;
    }
    const formData = new FormData(form);
    fetch('/configuracion/eliminar_tipo', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('columna-tipos').innerHTML = data.html;
            document.getElementById('columna-tarjetas').innerHTML = '<h5 id="tarjetas-anchor">Tarjetas</h5><div class="text-muted">Seleccione un tipo</div>';
            document.getElementById('columna-planes').innerHTML = '<h5 id="planes-anchor">Planes</h5><div class="text-muted">Seleccione una tarjeta</div>';
        } else {
            alert(data.error);
        }
    });
    return false;
}

// Funciones para la gestión de tarjetas
function seleccionarTarjeta(tipo, tarjeta) {
    // Refrescar columna de tarjetas con el seleccionado
    fetch(`/configuracion/columna_tarjetas?tipo=${encodeURIComponent(tipo)}&tarjeta=${encodeURIComponent(tarjeta)}`)
        .then(response => response.text())
        .then(html => {
            document.getElementById('columna-tarjetas').innerHTML = html;
            // Luego refrescar columna de planes
            fetch(`/configuracion/columna_planes?tipo=${encodeURIComponent(tipo)}&tarjeta=${encodeURIComponent(tarjeta)}`)
                .then(response => response.text())
                .then(html2 => {
                    document.getElementById('columna-planes').innerHTML = html2;
                });
        });
}

function agregarTarjetaAjax(form) {
    const formData = new FormData(form);
    fetch('/configuracion/agregar_tarjeta', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('columna-tarjetas').innerHTML = data.html;
            document.getElementById('columna-planes').innerHTML = '<h5 id="planes-anchor">Planes</h5><div class="text-muted">Seleccione una tarjeta</div>';
        } else {
            alert(data.error);
        }
    });
    return false;
}

function editarTarjetaAjax(form) {
    const formData = new FormData(form);
    fetch('/configuracion/editar_tarjeta', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('columna-tarjetas').innerHTML = data.html;
            document.getElementById('columna-planes').innerHTML = '<h5 id="planes-anchor">Planes</h5><div class="text-muted">Seleccione una tarjeta</div>';
        } else {
            alert(data.error);
        }
    });
    return false;
}

function eliminarTarjetaAjax(form) {
    if (!confirm('¿Está seguro de eliminar esta tarjeta?')) {
        return false;
    }
    const formData = new FormData(form);
    fetch('/configuracion/eliminar_tarjeta', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('columna-tarjetas').innerHTML = data.html;
            document.getElementById('columna-planes').innerHTML = '<h5 id="planes-anchor">Planes</h5><div class="text-muted">Seleccione una tarjeta</div>';
        } else {
            alert(data.error);
        }
    });
    return false;
}

// Funciones para la gestión de planes
function seleccionarPlan(tipo, tarjeta, planIdx) {
    fetch(`/configuracion/columna_planes?tipo=${encodeURIComponent(tipo)}&tarjeta=${encodeURIComponent(tarjeta)}&plan_idx=${planIdx}`)
        .then(response => response.text())
        .then(html => {
            document.getElementById('columna-planes').innerHTML = html;
        });
}

function agregarPlanAjax(form) {
    const formData = new FormData(form);
    const tipo = form.querySelector('input[name="tipo"]').value;
    const tarjeta = form.querySelector('input[name="tarjeta"]').value;
    fetch('/configuracion/agregar_plan', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('columna-planes').innerHTML = data.html;
            // Seleccionar automáticamente el plan agregado usando el índice devuelto por el backend
            if (typeof data.plan_idx !== 'undefined') {
                seleccionarPlan(tipo, tarjeta, data.plan_idx);
            }
            // Limpiar el formulario
            form.reset();
        } else {
            alert(data.error);
        }
    });
    return false;
}

function editarPlanAjax(form) {
    const formData = new FormData(form);
    const tipo = form.querySelector('input[name="tipo"]').value;
    const tarjeta = form.querySelector('input[name="tarjeta"]').value;
    fetch('/configuracion/editar_plan', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('columna-planes').innerHTML = data.html;
            // Mantener la selección en el plan editado usando el índice devuelto
            if (typeof data.plan_idx !== 'undefined' && data.plan_idx !== null) {
                seleccionarPlan(tipo, tarjeta, data.plan_idx);
            }
        } else {
            alert(data.error);
        }
    });
    return false;
}

function eliminarPlanAjax(tipo, tarjeta, planIdx) {
    if (!confirm('¿Está seguro de eliminar este plan?')) {
        return false;
    }
    const formData = new FormData();
    formData.append('tipo', tipo);
    formData.append('tarjeta', tarjeta);
    formData.append('plan_idx', planIdx);
    fetch('/configuracion/eliminar_plan', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('columna-planes').innerHTML = data.html;
            // Seleccionar el plan correcto usando el índice devuelto
            if (typeof data.plan_idx !== 'undefined' && data.plan_idx !== null) {
                seleccionarPlan(tipo, tarjeta, data.plan_idx);
            }
        } else {
            alert(data.error);
        }
    });
    return false;
}

function moverTipoAjax(tipo, direccion) {
    const formData = new FormData();
    formData.append('tipo', tipo);
    formData.append('direccion', direccion);
    fetch('/configuracion/mover_tipo', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('columna-tipos').innerHTML = data.html;
        } else {
            alert(data.error);
        }
    });
    return false;
}

function moverTarjetaAjax(tipo, tarjeta, direccion) {
    const formData = new FormData();
    formData.append('tipo', tipo);
    formData.append('tarjeta', tarjeta);
    formData.append('direccion', direccion);
    fetch('/configuracion/mover_tarjeta', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('columna-tarjetas').innerHTML = data.html;
        } else {
            alert(data.error);
        }
    });
    return false;
}

function moverPlanAjax(tipo, tarjeta, plan_idx, direccion) {
    const formData = new FormData();
    formData.append('tipo', tipo);
    formData.append('tarjeta', tarjeta);
    formData.append('plan_idx', plan_idx);
    formData.append('direccion', direccion);
    fetch('/configuracion/mover_plan', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            document.getElementById('columna-planes').innerHTML = data.html;
        } else {
            alert(data.error);
        }
    });
    return false;
}

// Delegación de eventos para formularios dinámicos en configuración
// Agregar tipo
document.addEventListener('submit', function(e) {
    if (e.target && e.target.matches('form[action="/configuracion/agregar_tipo"]')) {
        e.preventDefault();
        agregarTipoAjax(e.target);
    }
});
// Editar tipo
document.addEventListener('submit', function(e) {
    if (e.target && e.target.matches('form[action="/configuracion/editar_tipo"]')) {
        e.preventDefault();
        editarTipoAjax(e.target);
    }
});
// Eliminar tipo
document.addEventListener('submit', function(e) {
    if (e.target && e.target.matches('form[action="/configuracion/eliminar_tipo"]')) {
        e.preventDefault();
        eliminarTipoAjax(e.target);
    }
});
// Agregar tarjeta
document.addEventListener('submit', function(e) {
    if (e.target && e.target.matches('form[action="/configuracion/agregar_tarjeta"]')) {
        e.preventDefault();
        agregarTarjetaAjax(e.target);
    }
});
// Editar tarjeta
document.addEventListener('submit', function(e) {
    if (e.target && e.target.matches('form[action="/configuracion/editar_tarjeta"]')) {
        e.preventDefault();
        editarTarjetaAjax(e.target);
    }
});
// Eliminar tarjeta
document.addEventListener('submit', function(e) {
    if (e.target && e.target.matches('form[action="/configuracion/eliminar_tarjeta"]')) {
        e.preventDefault();
        eliminarTarjetaAjax(e.target);
    }
});
// Editar plan
document.addEventListener('submit', function(e) {
    if (e.target && e.target.matches('form[action="/configuracion/editar_plan"]')) {
        e.preventDefault();
        editarPlanAjax(e.target);
    }
}); 