# -*- coding: utf-8 -*-

# === Importaciones ===
import flet as ft
import database
import re
from functools import partial

# === Función Principal de la Aplicación ===
def main(page: ft.Page):
    
    # --- Inicialización de la Base de Datos ---
    database.create_table_if_not_exists()

    # --- Configuración de la Página Principal ---
    page.title = "Gestor de Tickets TKT e Intervinientes"
    page.vertical_alignment = ft.MainAxisAlignment.START
    page.horizontal_alignment = ft.CrossAxisAlignment.START
    page.window_width = 850
    page.window_height = 700

    # --- Manejo de Estado de la UI ---
    main_table_rows = {}
    interviniente_main_table_rows = {}
    productor_main_table_rows = {}

    # === Funciones de Lógica y Navegación de la UI (TKT) ===

    def show_view(search=False, form=False, results=False, main=False):
        search_bar.visible = not search
        search_field_container.visible = search
        form_view.visible = form
        results_view.visible = results
        main_data_view.visible = main
        page.update()

    def show_search_field(e):
        show_view(search=True)
        search_field.focus()

    def execute_search(e):
        search_term = search_field.value.strip()
        if not search_term:
            show_view()
            return
        found_results = database.search_tickets(search_term)
        if len(found_results) == 0:
            show_new_form(search_term)
        elif len(found_results) == 1:
            add_to_main_table(found_results[0])
            show_view(main=True)
        else:
            populate_results_table(found_results)
            show_view(results=True)
        search_field.value = ""

    def save_new_ticket(e):
        tkt_value = form_tkt.value.strip()
        if not validate_form(tkt_value):
            return
        new_ticket = database.insert_ticket(
            tkt=tkt_value,
            interno=form_interno.value.strip(),
            externo=form_externo.value.strip()
        )
        if new_ticket:
            add_to_main_table(new_ticket)
            show_view(main=True)

    def update_ticket_data(e):
        ticket_id = int(form_id_text.value)
        tkt_value = form_tkt.value.strip()
        if not validate_form(tkt_value, exclude_id=ticket_id):
            return
        updated_ticket = database.update_ticket(
            ticket_id=ticket_id,
            tkt=tkt_value,
            interno=form_interno.value.strip(),
            externo=form_externo.value.strip()
        )
        if updated_ticket:
            update_row_in_main_table(updated_ticket)
            show_view(main=True)

    def validate_form(tkt_value, exclude_id=None):
        is_valid = True
        if not tkt_value:
            form_tkt.error_text = "El campo TKT no puede estar vacío."
            is_valid = False
        elif not re.match(r"^[A-Z]{3,}-?[0-9]+$", tkt_value):
            form_tkt.error_text = "Formato: 3+ letras y números al final."
            is_valid = False
        elif database.check_ticket_exists(tkt_value, exclude_id=exclude_id):
            form_tkt.error_text = "Este número de TKT ya existe."
            is_valid = False
        else:
            form_tkt.error_text = ""
        form_tkt.update()
        return is_valid

    def add_to_main_table(ticket_data):
        ticket_id_str = str(ticket_data['id'])
        if ticket_id_str in main_table_rows:
            return
        new_row = ft.DataRow(
            cells=[
                ft.DataCell(ft.Checkbox(value=True)),
                ft.DataCell(ft.Text(ticket_id_str)),
                ft.DataCell(ft.Text(ticket_data['tkt'])),
                ft.DataCell(ft.Text(ticket_data['interno'])),
                ft.DataCell(ft.Text(ticket_data['externo'])),
                ft.DataCell(ft.Row([
                    ft.IconButton(icon=ft.Icons.EDIT, tooltip="Editar", on_click=partial(show_edit_form, ticket_data)),
                    ft.IconButton(icon=ft.Icons.DELETE, tooltip="Eliminar", on_click=partial(delete_ticket_from_view, ticket_id_str)),
                ])),
            ]
        )
        main_table_rows[ticket_id_str] = new_row
        main_datatable.rows.append(new_row)
        main_datatable.rows.sort(key=lambda r: r.cells[2].content.value)
        page.update()

    def update_row_in_main_table(ticket_data):
        ticket_id_str = str(ticket_data['id'])
        if ticket_id_str in main_table_rows:
            row_to_update = main_table_rows[ticket_id_str]
            row_to_update.cells[2].content.value = ticket_data['tkt']
            row_to_update.cells[3].content.value = ticket_data['interno']
            row_to_update.cells[4].content.value = ticket_data['externo']
            main_datatable.rows.sort(key=lambda r: r.cells[2].content.value)
            page.update()

    def delete_ticket_from_view(ticket_id_str, e):
        if ticket_id_str in main_table_rows:
            row_to_remove = main_table_rows.pop(ticket_id_str)
            main_datatable.rows.remove(row_to_remove)
            if not main_datatable.rows:
                show_view()
            else:
                page.update()

    def populate_results_table(results):
        results_datatable.rows.clear()
        for res in results:
            results_datatable.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.IconButton(icon=ft.Icons.ADD_TASK, tooltip="Seleccionar", on_click=partial(select_ticket_from_results, res))),
                    ft.DataCell(ft.Text(res['tkt'])),
                    ft.DataCell(ft.Text(res['interno'])),
                    ft.DataCell(ft.Text(res['externo']))
                ])
            )
        page.update()

    def select_ticket_from_results(ticket_data, e):
        add_to_main_table(ticket_data)
        show_view(main=True)

    def close_results_view(e):
        show_view()

    def show_new_form(search_term=""):
        form_title.value = "Crear Nuevo Ticket"
        form_id_text.visible = False
        form_save_button.visible = True
        form_edit_button.visible = False
        form_tkt.value = search_term.upper()
        form_interno.value = ""
        form_externo.value = ""
        form_tkt.error_text = ""
        show_view(form=True)

    def show_edit_form(ticket_data, e):
        form_title.value = "Editar Ticket"
        form_id_text.value = str(ticket_data['id'])
        form_id_text.visible = True
        form_save_button.visible = False
        form_edit_button.visible = True
        form_tkt.value = ticket_data['tkt']
        form_interno.value = ticket_data['interno']
        form_externo.value = ticket_data['externo']
        form_tkt.error_text = ""
        show_view(form=True)

    # === Definición de Controles de la UI (TKT) ===
    search_bar = ft.Row([ft.Text("TKT", size=20, weight=ft.FontWeight.BOLD), ft.IconButton(icon=ft.Icons.SEARCH, on_click=show_search_field, tooltip="Buscar TKT")], alignment=ft.MainAxisAlignment.START)
    search_field = ft.TextField(label="Nro de TKT", width=300, max_length=10, capitalization=ft.TextCapitalization.CHARACTERS, on_submit=execute_search)
    search_field_container = ft.Container(content=ft.Row([search_field], alignment=ft.MainAxisAlignment.START), visible=False)
    form_title = ft.Text(size=18, weight=ft.FontWeight.BOLD)
    form_id_text = ft.Text(weight=ft.FontWeight.BOLD)
    form_tkt = ft.TextField(label="TKT", width=300, max_length=10, capitalization=ft.TextCapitalization.CHARACTERS)
    form_interno = ft.TextField(label="Interno", multiline=True, min_lines=3, width=450)
    form_externo = ft.TextField(label="Externo", multiline=True, min_lines=3, width=450)
    form_save_button = ft.ElevatedButton(text="Guardar", on_click=save_new_ticket, icon=ft.Icons.SAVE)
    form_edit_button = ft.ElevatedButton(text="Editar", on_click=update_ticket_data, icon=ft.Icons.SAVE_AS)
    form_view = ft.Container(visible=False, padding=20, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=ft.border_radius.all(10),
        content=ft.Column(controls=[form_title, form_id_text, form_tkt, form_interno, form_externo, ft.Row([form_save_button, form_edit_button], alignment=ft.MainAxisAlignment.CENTER)], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER))
    results_datatable = ft.DataTable(columns=[ft.DataColumn(ft.Text("Seleccionar")), ft.DataColumn(ft.Text("TKT")), ft.DataColumn(ft.Text("Interno")), ft.DataColumn(ft.Text("Externo"))], rows=[])
    results_view = ft.Container(visible=False, padding=20, content=ft.Column(controls=[ft.Text("Resultados de la Búsqueda", size=18, weight=ft.FontWeight.BOLD), ft.Container(content=results_datatable, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=ft.border_radius.all(5)), ft.ElevatedButton(text="Cancelar", on_click=close_results_view)], horizontal_alignment=ft.CrossAxisAlignment.START, spacing=15))
    main_datatable = ft.DataTable(columns=[ft.DataColumn(ft.Text("")), ft.DataColumn(ft.Text("ID")), ft.DataColumn(ft.Text("TKT")), ft.DataColumn(ft.Text("Interno")), ft.DataColumn(ft.Text("Externo")), ft.DataColumn(ft.Text("Acciones"))], rows=[])
    main_data_view = ft.Container(visible=False, padding=20, content=ft.Column(controls=[ft.Text("Tickets Seleccionados", size=18, weight=ft.FontWeight.BOLD), ft.Container(content=main_datatable, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=ft.border_radius.all(5))], horizontal_alignment=ft.CrossAxisAlignment.START, spacing=15))

    # === Funciones de Lógica y Navegación de la UI (INTERVINIENTE) ===

    def show_interviniente_view(search=False, form=False, results=False, main=False):
        interviniente_search_bar.visible = not search
        interviniente_search_field_container.visible = search
        interviniente_form_view.visible = form
        interviniente_results_view.visible = results
        interviniente_main_data_view.visible = main
        page.update()

    def show_interviniente_search_field(e):
        show_interviniente_view(search=True)
        interviniente_search_field.focus()

    def execute_interviniente_search(e):
        search_term = interviniente_search_field.value.strip()
        if not search_term:
            show_interviniente_view()
            return
        found_results = database.search_intervinientes(search_term)
        if len(found_results) == 0:
            show_new_interviniente_form(search_term)
        elif len(found_results) == 1:
            add_to_interviniente_main_table(found_results[0])
            show_interviniente_view(main=True)
        else:
            populate_interviniente_results_table(found_results)
            show_interviniente_view(results=True)
        interviniente_search_field.value = ""

    def save_new_interviniente(e):
        interviniente_value = interviniente_form_tkt.value.strip()
        if not validate_interviniente_form(interviniente_value):
            return
        new_interviniente = database.insert_interviniente(
            interviniente=interviniente_value,
            interno=interviniente_form_interno.value.strip(),
            externo=interviniente_form_externo.value.strip()
        )
        if new_interviniente:
            add_to_interviniente_main_table(new_interviniente)
            show_interviniente_view(main=True)

    def update_interviniente_data(e):
        interviniente_id = int(interviniente_form_id_text.value)
        interviniente_value = interviniente_form_tkt.value.strip()
        if not validate_interviniente_form(interviniente_value, exclude_id=interviniente_id):
            return
        updated_interviniente = database.update_interviniente(
            interviniente_id=interviniente_id,
            interviniente=interviniente_value,
            interno=interviniente_form_interno.value.strip(),
            externo=interviniente_form_externo.value.strip()
        )
        if updated_interviniente:
            update_row_in_interviniente_main_table(updated_interviniente)
            show_interviniente_view(main=True)

    def validate_interviniente_form(interviniente_value, exclude_id=None):
        is_valid = True
        if not interviniente_value:
            interviniente_form_tkt.error_text = "El campo Interviniente no puede estar vacío."
            is_valid = False
        elif database.check_interviniente_exists(interviniente_value, exclude_id=exclude_id):
            interviniente_form_tkt.error_text = "Este Interviniente ya existe."
            is_valid = False
        else:
            interviniente_form_tkt.error_text = ""
        interviniente_form_tkt.update()
        return is_valid

    def add_to_interviniente_main_table(interviniente_data):
        interviniente_id_str = str(interviniente_data['id'])
        if interviniente_id_str in interviniente_main_table_rows:
            return
        new_row = ft.DataRow(
            cells=[
                ft.DataCell(ft.Checkbox(value=True)),
                ft.DataCell(ft.Text(interviniente_id_str)),
                ft.DataCell(ft.Text(interviniente_data['interviniente'])),
                ft.DataCell(ft.Text(interviniente_data['interno'])),
                ft.DataCell(ft.Text(interviniente_data['externo'])),
                ft.DataCell(ft.Row([
                    ft.IconButton(icon=ft.Icons.EDIT, tooltip="Editar", on_click=partial(show_edit_interviniente_form, interviniente_data)),
                    ft.IconButton(icon=ft.Icons.DELETE, tooltip="Eliminar", on_click=partial(delete_interviniente_from_view, interviniente_id_str)),
                ])),
            ]
        )
        interviniente_main_table_rows[interviniente_id_str] = new_row
        interviniente_main_datatable.rows.append(new_row)
        interviniente_main_datatable.rows.sort(key=lambda r: r.cells[2].content.value)
        page.update()

    def update_row_in_interviniente_main_table(interviniente_data):
        interviniente_id_str = str(interviniente_data['id'])
        if interviniente_id_str in interviniente_main_table_rows:
            row_to_update = interviniente_main_table_rows[interviniente_id_str]
            row_to_update.cells[2].content.value = interviniente_data['interviniente']
            row_to_update.cells[3].content.value = interviniente_data['interno']
            row_to_update.cells[4].content.value = interviniente_data['externo']
            interviniente_main_datatable.rows.sort(key=lambda r: r.cells[2].content.value)
            page.update()

    def delete_interviniente_from_view(interviniente_id_str, e):
        if interviniente_id_str in interviniente_main_table_rows:
            row_to_remove = interviniente_main_table_rows.pop(interviniente_id_str)
            interviniente_main_datatable.rows.remove(row_to_remove)
            if not interviniente_main_datatable.rows:
                show_interviniente_view()
            else:
                page.update()

    def populate_interviniente_results_table(results):
        interviniente_results_datatable.rows.clear()
        for res in results:
            interviniente_results_datatable.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.IconButton(icon=ft.Icons.ADD_TASK, tooltip="Seleccionar", on_click=partial(select_interviniente_from_results, res))),
                    ft.DataCell(ft.Text(res['interviniente'])),
                    ft.DataCell(ft.Text(res['interno'])),
                    ft.DataCell(ft.Text(res['externo']))
                ])
            )
        page.update()

    def select_interviniente_from_results(interviniente_data, e):
        add_to_interviniente_main_table(interviniente_data)
        show_interviniente_view(main=True)

    def close_interviniente_results_view(e):
        show_interviniente_view()

    def show_new_interviniente_form(search_term=""):
        interviniente_form_title.value = "Crear Nuevo Interviniente"
        interviniente_form_id_text.visible = False
        interviniente_form_save_button.visible = True
        interviniente_form_edit_button.visible = False
        interviniente_form_tkt.value = search_term.upper()
        interviniente_form_interno.value = ""
        interviniente_form_externo.value = ""
        interviniente_form_tkt.error_text = ""
        show_interviniente_view(form=True)

    def show_edit_interviniente_form(interviniente_data, e):
        interviniente_form_title.value = "Editar Interviniente"
        interviniente_form_id_text.value = str(interviniente_data['id'])
        interviniente_form_id_text.visible = True
        interviniente_form_save_button.visible = False
        interviniente_form_edit_button.visible = True
        interviniente_form_tkt.value = interviniente_data['interviniente']
        interviniente_form_interno.value = interviniente_data['interno']
        interviniente_form_externo.value = interviniente_data['externo']
        interviniente_form_tkt.error_text = ""
        show_interviniente_view(form=True)

    # === Definición de Controles de la UI (INTERVINIENTE) ===
    interviniente_search_bar = ft.Row([ft.Text("INTERVINIENTE", size=20, weight=ft.FontWeight.BOLD), ft.IconButton(icon=ft.Icons.SEARCH, on_click=show_interviniente_search_field, tooltip="Buscar Interviniente")], alignment=ft.MainAxisAlignment.START)
    interviniente_search_field = ft.TextField(label="Nombre del Interviniente", width=300, max_length=100, capitalization=ft.TextCapitalization.CHARACTERS, on_submit=execute_interviniente_search)
    interviniente_search_field_container = ft.Container(content=ft.Row([interviniente_search_field], alignment=ft.MainAxisAlignment.START), visible=False)
    interviniente_form_title = ft.Text(size=18, weight=ft.FontWeight.BOLD)
    interviniente_form_id_text = ft.Text(weight=ft.FontWeight.BOLD)
    interviniente_form_tkt = ft.TextField(label="Interviniente", width=300, max_length=100, capitalization=ft.TextCapitalization.CHARACTERS)
    interviniente_form_interno = ft.TextField(label="Interno", multiline=True, min_lines=3, width=450)
    interviniente_form_externo = ft.TextField(label="Externo", multiline=True, min_lines=3, width=450)
    interviniente_form_save_button = ft.ElevatedButton(text="Guardar", on_click=save_new_interviniente, icon=ft.Icons.SAVE)
    interviniente_form_edit_button = ft.ElevatedButton(text="Editar", on_click=update_interviniente_data, icon=ft.Icons.SAVE_AS)
    interviniente_form_view = ft.Container(visible=False, padding=20, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=ft.border_radius.all(10),
        content=ft.Column(controls=[interviniente_form_title, interviniente_form_id_text, interviniente_form_tkt, interviniente_form_interno, interviniente_form_externo, ft.Row([interviniente_form_save_button, interviniente_form_edit_button], alignment=ft.MainAxisAlignment.CENTER)], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER))
    interviniente_results_datatable = ft.DataTable(columns=[ft.DataColumn(ft.Text("Seleccionar")), ft.DataColumn(ft.Text("Interviniente")), ft.DataColumn(ft.Text("Interno")), ft.DataColumn(ft.Text("Externo"))], rows=[])
    interviniente_results_view = ft.Container(visible=False, padding=20, content=ft.Column(controls=[ft.Text("Resultados de la Búsqueda", size=18, weight=ft.FontWeight.BOLD), ft.Container(content=interviniente_results_datatable, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=ft.border_radius.all(5)), ft.ElevatedButton(text="Cancelar", on_click=close_interviniente_results_view)], horizontal_alignment=ft.CrossAxisAlignment.START, spacing=15))
    interviniente_main_datatable = ft.DataTable(columns=[ft.DataColumn(ft.Text("")), ft.DataColumn(ft.Text("ID")), ft.DataColumn(ft.Text("Interviniente")), ft.DataColumn(ft.Text("Interno")), ft.DataColumn(ft.Text("Externo")), ft.DataColumn(ft.Text("Acciones"))], rows=[])
    interviniente_main_data_view = ft.Container(visible=False, padding=20, content=ft.Column(controls=[ft.Text("Intervinientes Seleccionados", size=18, weight=ft.FontWeight.BOLD), ft.Container(content=interviniente_main_datatable, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=ft.border_radius.all(5))], horizontal_alignment=ft.CrossAxisAlignment.START, spacing=15))

    # === Funciones de Lógica y Navegación de la UI (PRODUCTOR) ===

    def show_productor_view(search=False, form=False, results=False, main=False):
        productor_search_bar.visible = not search
        productor_search_field_container.visible = search
        productor_form_view.visible = form
        productor_results_view.visible = results
        productor_main_data_view.visible = main
        page.update()

    def show_productor_search_field(e):
        show_productor_view(search=True)
        productor_search_field.focus()

    def execute_productor_search(e):
        search_term = productor_search_field.value.strip().upper()
        if not search_term:
            show_productor_view()
            return
        found_results = database.search_productores(search_term)
        if len(found_results) == 0:
            show_new_productor_form(search_term)
        elif len(found_results) == 1:
            add_to_productor_main_table(found_results[0])
            show_productor_view(main=True)
        else:
            populate_productor_results_table(found_results)
            show_productor_view(results=True)
        productor_search_field.value = ""

    def save_new_productor(e):
        nombre_value = productor_form_nombre.value.strip()
        codigo_value = productor_form_codigo.value.strip()
        if not validate_productor_form(nombre_value, codigo_value):
            return
        new_productor = database.insert_productor(
            nombre=nombre_value,
            codigo=codigo_value,
            interno=productor_form_interno.value.strip(),
            externo=productor_form_externo.value.strip()
        )
        if new_productor:
            add_to_productor_main_table(new_productor)
            show_productor_view(main=True)

    def update_productor_data(e):
        productor_id = int(productor_form_id_text.value)
        nombre_value = productor_form_nombre.value.strip()
        codigo_value = productor_form_codigo.value.strip()
        if not validate_productor_form(nombre_value, codigo_value, exclude_id=productor_id):
            return
        updated_productor = database.update_productor(
            productor_id=productor_id,
            nombre=nombre_value,
            codigo=codigo_value,
            interno=productor_form_interno.value.strip(),
            externo=productor_form_externo.value.strip()
        )
        if updated_productor:
            update_row_in_productor_main_table(updated_productor)
            show_productor_view(main=True)

    def validate_productor_form(nombre, codigo, exclude_id=None):
        is_valid = True
        # Validación de nombre
        if not nombre:
            productor_form_nombre.error_text = "El campo NOMBRE no puede estar vacío."
            is_valid = False
        else:
            productor_form_nombre.error_text = ""
        
        # Validación de código
        if not codigo:
            productor_form_codigo.error_text = "El campo CÓDIGO no puede estar vacío."
            is_valid = False
        elif not re.match(r"^\d{2}-\d{6}$", codigo):
            productor_form_codigo.error_text = "Formato incorrecto. Debe ser XX-XXXXXX."
            is_valid = False
        elif database.check_productor_exists(codigo, exclude_id=exclude_id):
            productor_form_codigo.error_text = "Este código de productor ya existe."
            is_valid = False
        else:
            productor_form_codigo.error_text = ""

        productor_form_nombre.update()
        productor_form_codigo.update()
        return is_valid

    def add_to_productor_main_table(productor_data):
        productor_id_str = str(productor_data['id'])
        if productor_id_str in productor_main_table_rows:
            return
        new_row = ft.DataRow(
            cells=[
                ft.DataCell(ft.Checkbox(value=True)),
                ft.DataCell(ft.Text(productor_id_str)),
                ft.DataCell(ft.Text(productor_data['nombre'])),
                ft.DataCell(ft.Text(productor_data['codigo'])),
                ft.DataCell(ft.Text(productor_data['interno'])),
                ft.DataCell(ft.Text(productor_data['externo'])),
                ft.DataCell(ft.Row([
                    ft.IconButton(icon=ft.Icons.EDIT, tooltip="Editar", on_click=partial(show_edit_productor_form, productor_data)),
                    ft.IconButton(icon=ft.Icons.DELETE, tooltip="Eliminar", on_click=partial(delete_productor_from_view, productor_id_str)),
                ])),
            ]
        )
        productor_main_table_rows[productor_id_str] = new_row
        productor_main_datatable.rows.append(new_row)
        productor_main_datatable.rows.sort(key=lambda r: r.cells[3].content.value) # Ordenar por código
        page.update()

    def update_row_in_productor_main_table(productor_data):
        productor_id_str = str(productor_data['id'])
        if productor_id_str in productor_main_table_rows:
            row_to_update = productor_main_table_rows[productor_id_str]
            row_to_update.cells[2].content.value = productor_data['nombre']
            row_to_update.cells[3].content.value = productor_data['codigo']
            row_to_update.cells[4].content.value = productor_data['interno']
            row_to_update.cells[5].content.value = productor_data['externo']
            productor_main_datatable.rows.sort(key=lambda r: r.cells[3].content.value)
            page.update()

    def delete_productor_from_view(productor_id_str, e):
        if productor_id_str in productor_main_table_rows:
            row_to_remove = productor_main_table_rows.pop(productor_id_str)
            productor_main_datatable.rows.remove(row_to_remove)
            if not productor_main_datatable.rows:
                show_productor_view()
            else:
                page.update()

    def populate_productor_results_table(results):
        productor_results_datatable.rows.clear()
        for res in results:
            productor_results_datatable.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.IconButton(icon=ft.Icons.ADD_TASK, tooltip="Seleccionar", on_click=partial(select_productor_from_results, res))),
                    ft.DataCell(ft.Text(res['nombre'])),
                    ft.DataCell(ft.Text(res['codigo'])),
                    ft.DataCell(ft.Text(res['interno'])),
                    ft.DataCell(ft.Text(res['externo']))
                ])
            )
        page.update()

    def select_productor_from_results(productor_data, e):
        add_to_productor_main_table(productor_data)
        show_productor_view(main=True)

    def close_productor_results_view(e):
        show_productor_view()

    def show_new_productor_form(search_term=""):
        productor_form_title.value = "Crear Nuevo Productor"
        productor_form_id_text.visible = False
        productor_form_save_button.visible = True
        productor_form_edit_button.visible = False
        
        # Determinar si el término de búsqueda es un código o un nombre
        if re.match(r"^\d{2}-\d{6}$", search_term):
            productor_form_codigo.value = search_term
            productor_form_nombre.value = ""
        else:
            productor_form_nombre.value = search_term.upper()
            productor_form_codigo.value = ""
            
        productor_form_interno.value = ""
        productor_form_externo.value = ""
        productor_form_nombre.error_text = ""
        productor_form_codigo.error_text = ""
        show_productor_view(form=True)

    def show_edit_productor_form(productor_data, e):
        productor_form_title.value = "Editar Productor"
        productor_form_id_text.value = str(productor_data['id'])
        productor_form_id_text.visible = True
        productor_form_save_button.visible = False
        productor_form_edit_button.visible = True
        productor_form_nombre.value = productor_data['nombre']
        productor_form_codigo.value = productor_data['codigo']
        productor_form_interno.value = productor_data['interno']
        productor_form_externo.value = productor_data['externo']
        productor_form_nombre.error_text = ""
        productor_form_codigo.error_text = ""
        show_productor_view(form=True)

    # === Definición de Controles de la UI (PRODUCTOR) ===
    productor_search_bar = ft.Row([ft.Text("PRODUCTOR", size=20, weight=ft.FontWeight.BOLD), ft.IconButton(icon=ft.Icons.SEARCH, on_click=show_productor_search_field, tooltip="Buscar Productor")], alignment=ft.MainAxisAlignment.START)
    productor_search_field = ft.TextField(label="Código o Nombre Productor", width=300, capitalization=ft.TextCapitalization.CHARACTERS, on_submit=execute_productor_search)
    productor_search_field_container = ft.Container(content=ft.Row([productor_search_field], alignment=ft.MainAxisAlignment.START), visible=False)
    productor_form_title = ft.Text(size=18, weight=ft.FontWeight.BOLD)
    productor_form_id_text = ft.Text(weight=ft.FontWeight.BOLD)
    productor_form_nombre = ft.TextField(label="NOMBRE", width=450, capitalization=ft.TextCapitalization.CHARACTERS)
    productor_form_codigo = ft.TextField(label="CODIGO", width=300, max_length=9)
    productor_form_interno = ft.TextField(label="Interno", multiline=True, min_lines=3, width=450)
    productor_form_externo = ft.TextField(label="Externo", multiline=True, min_lines=3, width=450)
    productor_form_save_button = ft.ElevatedButton(text="Guardar", on_click=save_new_productor, icon=ft.Icons.SAVE)
    productor_form_edit_button = ft.ElevatedButton(text="Editar", on_click=update_productor_data, icon=ft.Icons.SAVE_AS)
    productor_form_view = ft.Container(visible=False, padding=20, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=ft.border_radius.all(10),
        content=ft.Column(controls=[productor_form_title, productor_form_id_text, productor_form_nombre, productor_form_codigo, productor_form_interno, productor_form_externo, ft.Row([productor_form_save_button, productor_form_edit_button], alignment=ft.MainAxisAlignment.CENTER)], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER))
    productor_results_datatable = ft.DataTable(columns=[ft.DataColumn(ft.Text("Seleccionar")), ft.DataColumn(ft.Text("Nombre")), ft.DataColumn(ft.Text("Código")), ft.DataColumn(ft.Text("Interno")), ft.DataColumn(ft.Text("Externo"))], rows=[])
    productor_results_view = ft.Container(visible=False, padding=20, content=ft.Column(controls=[ft.Text("Resultados de la Búsqueda", size=18, weight=ft.FontWeight.BOLD), ft.Container(content=productor_results_datatable, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=ft.border_radius.all(5)), ft.ElevatedButton(text="Cancelar", on_click=close_productor_results_view)], horizontal_alignment=ft.CrossAxisAlignment.START, spacing=15))
    productor_main_datatable = ft.DataTable(columns=[ft.DataColumn(ft.Text("")), ft.DataColumn(ft.Text("ID")), ft.DataColumn(ft.Text("Nombre")), ft.DataColumn(ft.Text("Código")), ft.DataColumn(ft.Text("Interno")), ft.DataColumn(ft.Text("Externo")), ft.DataColumn(ft.Text("Acciones"))], rows=[])
    productor_main_data_view = ft.Container(visible=False, padding=20, content=ft.Column(controls=[ft.Text("Productores Seleccionados", size=18, weight=ft.FontWeight.BOLD), ft.Container(content=productor_main_datatable, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=ft.border_radius.all(5))], horizontal_alignment=ft.CrossAxisAlignment.START, spacing=15))

    # === Funciones de Lógica y Navegación de la UI (TEMA-ESTADO) ===

    def show_tema_estado_view(search=False, form=False, results=False, main=False):
        tema_estado_search_bar.visible = not search
        tema_estado_search_field_container.visible = search
        tema_estado_form_view.visible = form
        tema_estado_results_view.visible = results
        tema_estado_main_data_view.visible = main
        page.update()

    def show_tema_estado_search_field(e):
        show_tema_estado_view(search=True)
        tema_estado_search_field.focus()

    def execute_tema_estado_search(e):
        search_term = tema_estado_search_field.value.strip()
        if not search_term:
            show_tema_estado_view()
            return
        found_results = database.search_tema_estado(search_term)
        if len(found_results) == 0:
            show_new_tema_estado_form(search_term)
        elif len(found_results) == 1:
            add_to_tema_estado_main_table(found_results[0])
            show_tema_estado_view(main=True)
        else:
            populate_tema_estado_results_table(found_results)
            show_tema_estado_view(results=True)
        tema_estado_search_field.value = ""

    def save_new_tema_estado(e):
        tema_estado_value = tema_estado_form_tema_estado.value.strip()
        if not validate_tema_estado_form(tema_estado_value):
            return
        new_tema_estado = database.insert_tema_estado(
            tema_estado=tema_estado_value
        )
        if new_tema_estado:
            add_to_tema_estado_main_table(new_tema_estado)
            show_tema_estado_view(main=True)

    def update_tema_estado_data(e):
        tema_estado_id = int(tema_estado_form_id_text.value)
        tema_estado_value = tema_estado_form_tema_estado.value.strip()
        if not validate_tema_estado_form(tema_estado_value, exclude_id=tema_estado_id):
            return
        updated_tema_estado = database.update_tema_estado(
            tema_estado_id=tema_estado_id,
            tema_estado=tema_estado_value
        )
        if updated_tema_estado:
            update_row_in_tema_estado_main_table(updated_tema_estado)
            show_tema_estado_view(main=True)

    def validate_tema_estado_form(tema_estado_value, exclude_id=None):
        is_valid = True
        if not tema_estado_value:
            tema_estado_form_tema_estado.error_text = "El campo Tema-Estado no puede estar vacío."
            is_valid = False
        elif database.check_tema_estado_exists(tema_estado_value, exclude_id=exclude_id):
            tema_estado_form_tema_estado.error_text = "Este Tema-Estado ya existe."
            is_valid = False
        else:
            tema_estado_form_tema_estado.error_text = ""
        tema_estado_form_tema_estado.update()
        return is_valid

    def add_to_tema_estado_main_table(tema_estado_data):
        tema_estado_id_str = str(tema_estado_data['id'])
        if tema_estado_id_str in tema_estado_main_table_rows:
            return
        new_row = ft.DataRow(
            cells=[
                ft.DataCell(ft.Checkbox(value=True)),
                ft.DataCell(ft.Text(tema_estado_id_str)),
                ft.DataCell(ft.Text(tema_estado_data['temaestado'])),
                ft.DataCell(ft.Row([
                    ft.IconButton(icon=ft.Icons.EDIT, tooltip="Editar", on_click=partial(show_edit_tema_estado_form, tema_estado_data)),
                    ft.IconButton(icon=ft.Icons.DELETE, tooltip="Eliminar", on_click=partial(delete_tema_estado_from_view, tema_estado_id_str)),
                ])),
            ]
        )
        tema_estado_main_table_rows[tema_estado_id_str] = new_row
        tema_estado_main_datatable.rows.append(new_row)
        tema_estado_main_datatable.rows.sort(key=lambda r: r.cells[2].content.value)
        page.update()

    def update_row_in_tema_estado_main_table(tema_estado_data):
        tema_estado_id_str = str(tema_estado_data['id'])
        if tema_estado_id_str in tema_estado_main_table_rows:
            row_to_update = tema_estado_main_table_rows[tema_estado_id_str]
            row_to_update.cells[2].content.value = tema_estado_data['temaestado']
            tema_estado_main_datatable.rows.sort(key=lambda r: r.cells[2].content.value)
            page.update()

    def delete_tema_estado_from_view(tema_estado_id_str, e):
        if tema_estado_id_str in tema_estado_main_table_rows:
            row_to_remove = tema_estado_main_table_rows.pop(tema_estado_id_str)
            tema_estado_main_datatable.rows.remove(row_to_remove)
            if not tema_estado_main_datatable.rows:
                show_tema_estado_view()
            else:
                page.update()

    def populate_tema_estado_results_table(results):
        tema_estado_results_datatable.rows.clear()
        for res in results:
            tema_estado_results_datatable.rows.append(
                ft.DataRow(cells=[
                    ft.DataCell(ft.IconButton(icon=ft.Icons.ADD_TASK, tooltip="Seleccionar", on_click=partial(select_tema_estado_from_results, res))),
                    ft.DataCell(ft.Text(res['temaestado'])),
                ])
            )
        page.update()

    def select_tema_estado_from_results(tema_estado_data, e):
        add_to_tema_estado_main_table(tema_estado_data)
        show_tema_estado_view(main=True)

    def close_tema_estado_results_view(e):
        show_tema_estado_view()

    def show_new_tema_estado_form(search_term=""):
        tema_estado_form_title.value = "Crear Nuevo Tema-Estado"
        tema_estado_form_id_text.visible = False
        tema_estado_form_save_button.visible = True
        tema_estado_form_edit_button.visible = False
        tema_estado_form_tema_estado.value = search_term
        tema_estado_form_tema_estado.error_text = ""
        show_tema_estado_view(form=True)

    def show_edit_tema_estado_form(tema_estado_data, e):
        tema_estado_form_title.value = "Editar Tema-Estado"
        tema_estado_form_id_text.value = str(tema_estado_data['id'])
        tema_estado_form_id_text.visible = True
        tema_estado_form_save_button.visible = False
        tema_estado_form_edit_button.visible = True
        tema_estado_form_tema_estado.value = tema_estado_data['temaestado']
        tema_estado_form_tema_estado.error_text = ""
        show_tema_estado_view(form=True)

    # === Definición de Controles de la UI (TEMA-ESTADO) ===
    tema_estado_main_table_rows = {}
    tema_estado_search_bar = ft.Row([ft.Text("TEMA-ESTADO", size=20, weight=ft.FontWeight.BOLD), ft.IconButton(icon=ft.Icons.SEARCH, on_click=show_tema_estado_search_field, tooltip="Buscar Tema-Estado")], alignment=ft.MainAxisAlignment.START)
    tema_estado_search_field = ft.TextField(label="Tema-Estado", width=300, on_submit=execute_tema_estado_search)
    tema_estado_search_field_container = ft.Container(content=ft.Row([tema_estado_search_field], alignment=ft.MainAxisAlignment.START), visible=False)
    tema_estado_form_title = ft.Text(size=18, weight=ft.FontWeight.BOLD)
    tema_estado_form_id_text = ft.Text(weight=ft.FontWeight.BOLD)
    tema_estado_form_tema_estado = ft.TextField(label="Tema-Estado", width=450)
    tema_estado_form_save_button = ft.ElevatedButton(text="Guardar", on_click=save_new_tema_estado, icon=ft.Icons.SAVE)
    tema_estado_form_edit_button = ft.ElevatedButton(text="Editar", on_click=update_tema_estado_data, icon=ft.Icons.SAVE_AS)
    tema_estado_form_view = ft.Container(visible=False, padding=20, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=ft.border_radius.all(10),
        content=ft.Column(controls=[tema_estado_form_title, tema_estado_form_id_text, tema_estado_form_tema_estado, ft.Row([tema_estado_form_save_button, tema_estado_form_edit_button], alignment=ft.MainAxisAlignment.CENTER)], spacing=15, horizontal_alignment=ft.CrossAxisAlignment.CENTER))
    tema_estado_results_datatable = ft.DataTable(columns=[ft.DataColumn(ft.Text("Seleccionar")), ft.DataColumn(ft.Text("Tema-Estado"))], rows=[])
    tema_estado_results_view = ft.Container(visible=False, padding=20, content=ft.Column(controls=[ft.Text("Resultados de la Búsqueda", size=18, weight=ft.FontWeight.BOLD), ft.Container(content=tema_estado_results_datatable, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=ft.border_radius.all(5)), ft.ElevatedButton(text="Cancelar", on_click=close_tema_estado_results_view)], horizontal_alignment=ft.CrossAxisAlignment.START, spacing=15))
    tema_estado_main_datatable = ft.DataTable(columns=[ft.DataColumn(ft.Text("")), ft.DataColumn(ft.Text("ID")), ft.DataColumn(ft.Text("Tema-Estado")), ft.DataColumn(ft.Text("Acciones"))], rows=[])
    tema_estado_main_data_view = ft.Container(visible=False, padding=20, content=ft.Column(controls=[ft.Text("Tema-Estado Seleccionados", size=18, weight=ft.FontWeight.BOLD), ft.Container(content=tema_estado_main_datatable, border=ft.border.all(1, ft.Colors.GREY_300), border_radius=ft.border_radius.all(5))], horizontal_alignment=ft.CrossAxisAlignment.START, spacing=15))

    # === Montaje Final de la Página ===
    page.add(
        search_bar, 
        search_field_container, 
        form_view, 
        results_view, 
        main_data_view, 
        ft.Divider(),
        interviniente_search_bar,
        interviniente_search_field_container,
        interviniente_form_view,
        interviniente_results_view,
        interviniente_main_data_view,
        ft.Divider(),
        productor_search_bar,
        productor_search_field_container,
        productor_form_view,
        productor_results_view,
        productor_main_data_view,
        ft.Divider(),
        tema_estado_search_bar,
        tema_estado_search_field_container,
        tema_estado_form_view,
        tema_estado_results_view,
        tema_estado_main_data_view,
    )
    
    # Establece el estado inicial de la vista.
    show_view()
    show_interviniente_view()
    show_productor_view()
    show_tema_estado_view()

# === Punto de Entrada para Ejecutar la Aplicación ===
ft.app(target=main, view=ft.AppView.WEB_BROWSER)