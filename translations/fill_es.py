"""Rellena las traducciones vacías del archivo `.ts` español.

El inglés es el idioma fuente del programa; este script solo traduce los mensajes que
todavía no tienen texto. Se usa una vez por idioma y después se revisa el resultado en Qt
Linguist. No pisa traducciones ya escritas.
"""

from __future__ import annotations

import sys
import xml.etree.ElementTree as ET
from pathlib import Path

TS = Path(__file__).resolve().parent / "luciotech_es.ts"

ES: dict[str, str] = {
    "Budget line": "Línea de presupuesto",
    "Type": "Tipo",
    "Description": "Descripción",
    "Quantity": "Cantidad",
    "Unit price": "Precio unitario",
    "Add line": "Añadir línea",
    "Edit line": "Editar línea",
    "Remove line": "Quitar línea",
    "Budget": "Presupuesto",
    "Totals": "Totales",
    "Subtotal": "Subtotal",
    "Discount": "Descuento",
    "Tax": "IVA",
    "Deposit (reception)": "Anticipo (recepción)",
    "Payments received": "Pagos recibidos",
    "Total": "Total",
    "Outstanding balance": "Saldo pendiente",
    "Record payment": "Registrar pago",
    "Void payment": "Anular pago",
    "Payments": "Pagos",
    "The order no longer exists.": "La orden ya no existe.",
    "Voided": "Anulado",
    "Current": "Vigente",
    "Tax (disabled)": "IVA (desactivado)",
    "Select a line.": "Seleccione una línea.",
    "Select a payment.": "Seleccione un pago.",
    "Reason for voiding (optional):": "Motivo de la anulación (opcional):",
    "Could not save. Please try again.": "No se pudo guardar. Intente de nuevo.",
    "Saved.": "Guardado.",
    "Change my password": "Cambiar mi contraseña",
    "Current password": "Contraseña actual",
    "New password": "Contraseña nueva",
    "Repeat the new password": "Repetir la nueva",
    "The two new passwords do not match.": "Las dos contraseñas nuevas no coinciden.",
    "The user no longer exists.": "El usuario ya no existe.",
    "The password could not be changed. Please try again.": (
        "No se pudo cambiar la contraseña. Intente de nuevo."
    ),
    "Edit customer": "Editar cliente",
    "New customer": "Nuevo cliente",
    "Address": "Dirección",
    "Notes": "Notas",
    "The customer could not be saved. Check the details and try again.": (
        "No se pudo guardar el cliente. Revise los datos e intente de nuevo."
    ),
    "Customers with the same ID or phone already exist:\n\n%1\n\nDo you want to save anyway?": (
        "Ya existen clientes con la misma identificación o teléfono:\n\n%1\n\n"
        "¿Desea guardar de todos modos?"
    ),
    "Search by name, ID or phone": "Buscar por nombre, identificación o teléfono",
    "Edit": "Editar",
    "Full name": "Nombre completo",
    "ID number": "Identificación",
    "Phone": "Teléfono",
    "Email": "Correo electrónico",
    "Select a customer from the list.": "Seleccione un cliente en la lista.",
    "Order documents": "Documentos de la orden",
    "Choose the document to print or save:": "Elija el documento que quiere imprimir o guardar:",
    "Edit equipment": "Editar equipo",
    "New equipment": "Nuevo equipo",
    "Optional": "Opcional",
    "Show": "Mostrar",
    "Brand": "Marca",
    "Model": "Modelo",
    "Serial number": "Número de serie",
    "Colour": "Color",
    "Operating system": "Sistema operativo",
    "Password or PIN": "Contraseña o PIN",
    "Accessories received": "Accesorios recibidos",
    "Physical condition": "Estado físico",
    "Reported problem": "Problema reportado",
    "Intake notes": "Observaciones de ingreso",
    "Hide": "Ocultar",
    "The equipment could not be saved. Check the details and try again.": (
        "No se pudo guardar el equipo. Revise los datos e intente de nuevo."
    ),
    "The serial number already appears in these orders: %1.\n\nDo you want to save anyway?": (
        "El número de serie ya aparece en las órdenes: %1.\n\n¿Desea guardar de todos modos?"
    ),
    "Customer": "Cliente",
    "Equipment type": "Tipo de equipo",
    "First register a customer on the Customers tab.": (
        "Primero registre un cliente en la pestaña Clientes."
    ),
    "Select a piece of equipment from the list.": "Seleccione un equipo en la lista.",
    "Find and replace": "Buscar y reemplazar",
    "Text to find": "Texto a buscar",
    "Replace with": "Reemplazar con",
    "Match case": "Distinguir mayúsculas",
    "Find next": "Buscar siguiente",
    "Replace": "Reemplazar",
    "Replace all": "Reemplazar todo",
    "Close": "Cerrar",
    "Find": "Buscar",
    "Match found.": "Coincidencia encontrada.",
    "No more matches.": "Sin más coincidencias.",
    "Replaced.": "Reemplazado.",
    "%1 replacements.": "%1 reemplazos.",
    "Create the first user": "Crear el primer usuario",
    "Welcome to %1": "Bienvenido a %1",
    "There is no account on this computer yet. Create the workshop administrator account: it will appear on the documents you print and it can add the other technicians later from File ▸ Users.": (
        "Todavía no hay ninguna cuenta en este equipo. Cree la del administrador del taller: "
        "será la que aparezca en los documentos que imprima y la que podrá añadir a los demás "
        "técnicos después, desde Archivo ▸ Usuarios."
    ),
    "First and last name, as it should be printed": (
        "Nombre y apellido, como debe salir impreso"
    ),
    "Used to sign in; no spaces or accents": "Para entrar; sin espacios ni tildes",
    "User": "Usuario",
    "Password": "Contraseña",
    "Repeat password": "Repetir contraseña",
    "The two passwords do not match.": "Las dos contraseñas no coinciden.",
    "The user could not be created. Please try again.": (
        "No se pudo crear el usuario. Intente de nuevo."
    ),
    "Workshop summary": "Resumen del taller",
    "Equipment received today": "Equipos recibidos hoy",
    "Pending diagnosis": "Pendientes de diagnóstico",
    "Under repair": "En reparación",
    "Awaiting approval": "Esperando aprobación",
    "Ready for delivery": "Listos para entregar",
    "Delivered this month": "Entregados este mes",
    "Income this month": "Ingresos del mes",
    "Sign in": "Entrar",
    "Choose your user and enter your password to open the workshop.": (
        "Elija su usuario y escriba su contraseña para abrir el taller."
    ),
    "Show password": "Mostrar contraseña",
    "Quit": "Salir",
    "There is no active user to sign in.": "No hay ningún usuario activo para entrar.",
    "Enter your password.": "Escriba la contraseña.",
    "Incorrect user or password.": "Usuario o contraseña incorrectos.",
    "Could not check the credentials. Please try again.": (
        "No se pudo comprobar el acceso. Intente de nuevo."
    ),
    "Invalid equipment details.": "Datos de equipo no válidos.",
    "Equipment not found.": "Equipo no encontrado.",
    "Invalid budget line.": "Línea de presupuesto no válida.",
    "Invalid payment details.": "Datos de pago no válidos.",
    "The note title is required.": "El título de la nota es obligatorio.",
    "The user name must have at least {count} characters.": (
        "El nombre de usuario debe tener al menos {count} caracteres."
    ),
    "The user name cannot be longer than {count} characters.": (
        "El nombre de usuario no puede pasar de {count} caracteres."
    ),
    "The user name may only contain unaccented letters, digits, dot, hyphen and underscore.": (
        "El nombre de usuario solo puede llevar letras sin tilde, números, punto, guion y "
        "guion bajo."
    ),
    "The password must have at least {count} characters.": (
        "La contraseña debe tener al menos {count} caracteres."
    ),
    "The password cannot be longer than {count} characters.": (
        "La contraseña no puede pasar de {count} caracteres."
    ),
    "The full name cannot be empty.": "El nombre completo no puede estar vacío.",
    "The full name cannot be longer than 120 characters.": (
        "El nombre completo no puede pasar de 120 caracteres."
    ),
    "A user with that sign-in name already exists.": (
        "Ya existe un usuario con ese nombre de acceso."
    ),
    "The current password is not correct.": "La contraseña actual no es correcta.",
    "At least one active administrator must remain.": (
        "Debe quedar al menos un administrador activo."
    ),
    "Users have already been created on this computer.": (
        "Ya hay usuarios creados en este equipo."
    ),
    "Invalid tax percentage: {value}": "Porcentaje de impuesto no válido: {value}",
    "The tax percentage must be between 0 and 100.": (
        "El porcentaje de impuesto debe estar entre 0 y 100."
    ),
    "Budget validity must be greater than zero days.": (
        "La validez del presupuesto debe ser mayor que cero días."
    ),
    "Invalid paper size: {value}": "Tamaño de papel no válido: {value}",
    "Margins must be between {min} and {max} mm.": (
        "Los márgenes deben estar entre {min} y {max} mm."
    ),
    "Warranty days cannot be negative.": "Los días de garantía no pueden ser negativos.",
    "The collection deadline must be greater than zero.": (
        "El plazo de retirada debe ser mayor que cero."
    ),
    "Invalid reception details.": "Datos de recepción no válidos.",
    "Customer not found.": "Cliente no encontrado.",
    "Invalid customer details.": "Datos de cliente no válidos.",
    "Received": "Recibido",
    "Diagnosed": "Diagnosticado",
    "Waiting for parts": "Esperando repuesto",
    "Repaired": "Reparado",
    "Delivered": "Entregado",
    "Not repairable": "No reparable",
    "Cancelled": "Cancelado",
    "Low": "Baja",
    "Normal": "Normal",
    "High": "Alta",
    "Urgent": "Urgente",
    "Condition on arrival": "Estado al recibir",
    "Accessories": "Accesorios",
    "Physical damage": "Daño físico",
    "Repair in progress": "Proceso de reparación",
    "Repaired equipment": "Equipo reparado",
    "Other": "Otro",
    "Deposit": "Anticipo",
    "Part payment": "Abono",
    "Final payment": "Pago final",
    "Refund": "Reembolso",
    "Cash": "Efectivo",
    "Bank transfer": "Transferencia bancaria",
    "Card": "Tarjeta",
    "Bank deposit": "Depósito",
    "Administrator": "Administrador",
    "Technician": "Técnico",
    "Diagnosis": "Diagnóstico",
    "Labour": "Mano de obra",
    "Part": "Repuesto",
    "Accessory": "Accesorio",
    "Service": "Servicio",
    "Call to customer": "Llamada al cliente",
    "Message sent": "Mensaje enviado",
    "Budget approved": "Presupuesto aprobado",
    "Budget rejected": "Presupuesto rechazado",
    "Part requested": "Repuesto solicitado",
    "Part received": "Repuesto recibido",
    "Diagnosis updated": "Diagnóstico actualizado",
    "Payment received": "Pago recibido",
    "Payment voided": "Pago anulado",
    "Equipment delivered": "Equipo entregado",
    "Internal note": "Nota interna",
    "Order deleted": "Orden eliminada",
    "Order restored": "Orden restaurada",
    "State change": "Cambio de estado",
    "Equipment delivered to the customer": "Equipo entregado al cliente",
    "Name": "Nombre",
    "Primary phone": "Teléfono principal",
    "Secondary phone": "Teléfono secundario",
    "Other orders": "Otras órdenes",
    "Total outstanding balance": "Saldo pendiente total",
    "Order number": "Número de orden",
    "Status": "Estado",
    "Priority": "Prioridad",
    "Equipment": "Equipo",
    "Received on": "Fecha de ingreso",
    "Estimated date": "Fecha estimada",
    "Delivery date": "Fecha de entrega",
    "Technician in charge": "Técnico responsable",
    "The line no longer exists.": "La línea ya no existe.",
    "The payment no longer exists.": "El pago ya no existe.",
    "Unknown document: {kind}": "Documento desconocido: {kind}",
    "Equipment received": "Equipo recibido",
    "Brand and model": "Marca y modelo",
    "Reception": "Recepción",
    "Estimated delivery": "Entrega estimada",
    "Customer signature": "Firma del cliente",
    "Workshop signature": "Firma del taller",
    "Budget details": "Detalle del presupuesto",
    "Item": "Concepto",
    "Qty.": "Cant.",
    "Amount": "Importe",
    "Budget valid for {days} days from {date}. Work starts once approved.": (
        "Presupuesto válido por {days} días desde el {date}. El trabajo se inicia una vez "
        "aprobado."
    ),
    "Customer approval": "Aprobación del cliente",
    "Name: {signature}   Date: ______________": (
        "Nombre: {signature}   Fecha: ______________"
    ),
    "Signature: {signature}": "Firma: {signature}",
    "Physical condition on arrival": "Estado físico al recibir",
    "Order": "Orden",
    "Current status": "Estado actual",
    "Technical diagnosis": "Diagnóstico técnico",
    "Work performed": "Trabajo realizado",
    "Parts used": "Repuestos utilizados",
    "Recommendations": "Recomendaciones",
    "Photographs of the equipment on arrival": "Fotografías del equipo al recibir",
    "Photographs of the repaired equipment": "Fotografías del equipo reparado",
    "Warranty": "Garantía",
    "Technician signature": "Firma del técnico",
    "Final status": "Estado final",
    "Coverage": "Cobertura",
    "Scope": "Alcance",
    "Covers only the work performed and the parts invoiced.": (
        "Cubre únicamente el trabajo realizado y los repuestos facturados."
    ),
    "Declaration of conformity": "Declaración de conformidad",
    "I received the equipment in the condition described, tested and working, and I accept the warranty coverage stated above.": (
        "Recibí el equipo en las condiciones descritas, probado y funcionando, y acepto el "
        "alcance de la garantía indicada."
    ),
    "Event": "Evento",
    "Movements": "Movimientos",
    "Date": "Fecha",
    "Detail": "Detalle",
    "Generated on {date}": "Generado el {date}",
    "{footer} by {user}": "{footer} por {user}",
    "Diagnosis cost": "Costo de diagnóstico",
    "Budget lines": "Líneas de presupuesto",
    "Tax ({percent}%)": "IVA ({percent}%)",
    "Deposit received": "Anticipo recibido",
    "Amounts": "Importes",
    "Method": "Método",
    "No warranty recorded": "Sin garantía registrada",
    "{days} days": "{days} días",
    "Photographs of the equipment": "Fotografías del equipo",
    "Terms and conditions": "Términos y condiciones",
    "Warranty conditions": "Condiciones de garantía",
    "Home": "Inicio",
    "Orders": "Órdenes",
    "Customers": "Clientes",
    "Trash": "Papelera",
    "Signed in: %1 · %2": "Sesión: %1 · %2",
    "This name appears in the order history and in the footer of the documents you print.": (
        "Este nombre aparece en el historial de las órdenes y en el pie de los documentos "
        "que imprima."
    ),
    "&File": "&Archivo",
    "Change &my password…": "Cambiar &mi contraseña…",
    "&Settings…": "&Configuración…",
    "&Users…": "&Usuarios…",
    "&Sign out": "&Cerrar sesión",
    "&Quit": "&Salir",
    "No pending actions": "Sin acciones pendientes",
    "Start diagnosis": "Iniciar diagnóstico",
    "The equipment is already in the workshop: move it to the diagnosis queue.": (
        "El equipo ya está en el taller: pásalo a la cola de diagnóstico."
    ),
    "Mark as diagnosed": "Marcar como diagnosticado",
    "Write the diagnosis on the Work tab first.": (
        "Escribe antes el diagnóstico en la pestaña Trabajo."
    ),
    "Give the budget to the customer": "Entregar presupuesto al cliente",
    "The order awaits approval and the budget opens for printing.": (
        "La orden espera la aprobación y se abre el presupuesto para imprimir."
    ),
    "Start the repair": "Iniciar reparación",
    "With the budget approved, start working on the equipment.": (
        "Con el presupuesto aprobado, empieza el trabajo en el equipo."
    ),
    "Resume the repair": "Reanudar la reparación",
    "The part has arrived: get back to work on the equipment.": (
        "El repuesto llegó: vuelve al trabajo en el equipo."
    ),
    "Mark as repaired": "Marcar como reparado",
    "When the equipment works, mark it and hand over the technical report.": (
        "Cuando el equipo funcione, márcalo y entrega el informe técnico."
    ),
    "Tell the customer the equipment is ready to be collected.": (
        "Avisa al cliente de que puede recoger el equipo."
    ),
    "Deliver the equipment": "Entregar el equipo",
    "Collect any balance due and hand over the receipt with the delivery date.": (
        "Cobra lo que falte y entrega el comprobante con la fecha de entrega."
    ),
    "Print the delivery receipt": "Imprimir comprobante de entrega",
    "The order is closed: reprint the receipt whenever needed.": (
        "La orden está cerrada: reimprime el comprobante cuando haga falta."
    ),
    "Print the technical report": "Imprimir informe técnico",
    "The equipment cannot be repaired: hand over the report and return it.": (
        "El equipo no se repara: entrega el informe y devuélvelo al cliente."
    ),
    "The order is cancelled: only the history remains.": (
        "La orden está cancelada: solo queda el historial."
    ),
    "Service order": "Orden de servicio",
    "Change comment (optional)": "Comentario del cambio (opcional)",
    "Change status": "Cambiar estado",
    "Note title": "Título de la nota",
    "Detail (optional)": "Detalle (opcional)",
    "Add note": "Añadir nota",
    "Actions": "Acciones",
    "Next step": "Siguiente paso",
    "Repair": "Reparación",
    "Customer recommendations": "Recomendaciones al cliente",
    "Photographs": "Fotografías",
    "Summary": "Resumen",
    "Work": "Trabajo",
    "Money": "Dinero",
    "History": "Historial",
    "Documents…": "Documentos…",
    "Print or save the order documents as PDF": (
        "Imprimir o guardar en PDF los documentos de la orden"
    ),
    "Delete order": "Eliminar orden",
    "Save texts": "Guardar textos",
    "Hide password": "Ocultar contraseña",
    "The texts could not be saved: %1": "No se pudieron guardar los textos: %1",
    "Texts saved.": "Textos guardados.",
    "Changes saved automatically.": "Cambios guardados automáticamente.",
    "The clinical texts could not be saved. Close anyway?": (
        "No se pudieron guardar los textos clínicos. ¿Cerrar de todos modos?"
    ),
    "Mark the order as delivered?": "¿Marcar la orden como entregada?",
    "Preview: {document}.": "Vista previa: {document}.",
    "The order will be sent to the trash and will no longer appear in the list. You can restore it from the Trash tab.\n\nDo you want to continue?": (
        "La orden se enviará a la papelera y dejará de aparecer en la lista. Podrá "
        "restaurarla desde la pestaña Papelera.\n\n¿Desea continuar?"
    ),
    "The order could not be deleted. Please try again.": (
        "No se pudo eliminar. Intente de nuevo."
    ),
    "Number, customer, phone, serial, brand or model": (
        "Número, cliente, teléfono, serie, marca o modelo"
    ),
    "With an outstanding balance": "Con saldo pendiente",
    "New reception": "Nueva recepción",
    "Delete": "Eliminar",
    "Sends the selected order to the trash": "Envía la orden seleccionada a la papelera",
    "All statuses": "Todos los estados",
    "All priorities": "Todas las prioridades",
    "All types": "Todos los tipos",
    "Select an order from the list.": "Seleccione una orden de la lista.",
    "Order %1 will be sent to the trash and will no longer appear in the list. You can restore it from the Trash tab.\n\nDo you want to continue?": (
        "La orden %1 se enviará a la papelera y dejará de aparecer en la lista. Podrá "
        "restaurarla desde la pestaña Papelera.\n\n¿Desea continuar?"
    ),
    "Reception recorded": "Recepción registrada",
    "The reception was recorded with number %1.": (
        "La recepción quedó registrada con el número %1."
    ),
    "Print receipt": "Imprimir comprobante",
    "Open order": "Abrir orden",
    "Reference": "Referencia",
    "Edit photograph": "Editar fotografía",
    "Import…": "Importar…",
    "Paste": "Pegar",
    "View": "Ver",
    "Rotate left": "Rotar izquierda",
    "Rotate right": "Rotar derecha",
    "Edit…": "Editar…",
    "Remove": "Quitar",
    "Move up": "Subir",
    "Move down": "Bajar",
    "View photograph": "Ver fotografía",
    "The image could not be loaded.": "No se pudo cargar la imagen.",
    "Import photographs": "Importar fotografías",
    "Paste photograph": "Pegar fotografía",
    "Rotate photograph": "Rotar fotografía",
    "Remove photograph": "Quitar fotografía",
    "Remove the selected photograph? The file will be deleted too.": (
        "¿Quitar la fotografía seleccionada? El archivo también se borrará."
    ),
    "Reported problem *": "Problema reportado *",
    "Received date and time": "Fecha y hora de ingreso",
    "Estimated delivery date": "Fecha estimada de entrega",
    "Initial diagnosis cost": "Costo inicial de diagnóstico",
    "Other accessories:": "Otros accesorios:",
    "— New customer —": "— Cliente nuevo —",
    "Model or details": "Modelo o detalle",
    "— New equipment —": "— Equipo nuevo —",
    "The reception could not be recorded. Please try again.": (
        "No se pudo registrar la recepción. Intente de nuevo."
    ),
    "Similar customer: %1": "Cliente parecido: %1",
    "Same serial number on order %1": "Mismo número de serie en la orden %1",
    "Do you want to record the reception anyway?": (
        "¿Desea registrar la recepción de todos modos?"
    ),
    "Bold": "Negrita",
    "Italic": "Cursiva",
    "Underline": "Subrayado",
    "Strikethrough": "Tachado",
    "Bullet list": "Lista con viñetas",
    "Numbered list": "Lista numerada",
    "Increase indent": "Aumentar sangría",
    "Decrease indent": "Disminuir sangría",
    "Align left": "Alinear a la izquierda",
    "Centre": "Centrar",
    "Align right": "Alinear a la derecha",
    "Justify": "Justificar",
    "Text colour": "Color del texto",
    "Background colour": "Color de fondo",
    "Clear formatting": "Quitar formato",
    "Cut": "Cortar",
    "Copy": "Copiar",
    "Paste as plain text": "Pegar como texto sin formato",
    "Insert horizontal line": "Insertar línea horizontal",
    "Insert table": "Insertar tabla",
    "Insert image": "Insertar imagen",
    "Print preview": "Vista previa de impresión",
    "Undo": "Deshacer",
    "Redo": "Rehacer",
    "Font": "Fuente",
    "Size": "Tamaño",
    "Zoom out": "Alejar",
    "Zoom in": "Acercar",
    "Rows:": "Filas:",
    "Columns:": "Columnas:",
    "Images (*.jpg *.jpeg *.png *.webp *.bmp)": (
        "Imágenes (*.jpg *.jpeg *.png *.webp *.bmp)"
    ),
    "Predefined texts": "Textos predefinidos",
    "Insert a predefined phrase": "Insertar una frase predefinida",
    "(No predefined texts configured)": "(No hay textos configurados)",
    "Change password": "Cambiar contraseña",
    "Settings": "Configuración",
    "Tax enabled": "IVA activo",
    "Workshop name": "Nombre del taller",
    "Tax percentage": "Porcentaje de IVA",
    "Language": "Idioma",
    "These details appear in the header of every document. Workshop prices already include tax, so tax starts disabled.": (
        "Estos datos salen en la cabecera de todos los documentos. Los precios del taller ya "
        "llevan el impuesto incluido, así que el IVA nace desactivado."
    ),
    " days": " días",
    " months": " meses",
    "Paper size": "Tamaño de papel",
    "Page margins": "Márgenes de la hoja",
    "Budget validity": "Validez del presupuesto",
    "Deadline to collect equipment": "Plazo para retirar un equipo",
    "Equipment types (one per line)": "Tipos de equipo (uno por línea)",
    "The collection deadline replaces the {meses} placeholder in the terms and conditions. If the type list is left empty, the default values return.": (
        "El plazo de retirada sustituye al marcador {meses} de los términos y condiciones. "
        "Si la lista de tipos se deja vacía, vuelven los valores por defecto."
    ),
    "Restore default text": "Restablecer texto por defecto",
    "Warranty days (new orders and orders without their own warranty)": (
        "Días de garantía (órdenes nuevas y sin plazo propio)"
    ),
    "Terms and conditions: printed on the four documents handed to the customer. The {meses} placeholder is replaced by the deadline from Documents.": (
        "Términos y condiciones: se imprimen en los cuatro documentos que se entregan al "
        "cliente. El marcador {meses} se sustituye por el plazo de Documentos."
    ),
    "Warranty conditions: same documents, placeholders {dias}, {orden} and {meses}. Leaving the text empty removes the section.": (
        "Condiciones de garantía: mismos documentos, marcadores {dias}, {orden} y {meses}. "
        "Dejar el texto vacío quita el apartado."
    ),
    "An order with its own days keeps its warranty; one without uses the value here. Setting 0 days removes the warranty from every document.": (
        "Una orden con días propios conserva su plazo; la que no tiene usa el de aquí. Poner "
        "0 días quita la garantía de todos los documentos."
    ),
    "The settings could not be read: %1": "No se pudo leer la configuración: %1",
    "The settings could not be saved: %1": "No se pudo guardar la configuración: %1",
    "The language takes effect the next time the application starts.": (
        "El idioma se aplicará la próxima vez que se abra la aplicación."
    ),
    "Restore": "Restaurar",
    "Returns the selected order to the list": "Devuelve la orden seleccionada a la lista",
    "Open": "Abrir",
    "Deleted orders are not removed from the database: they stay here until you restore them.": (
        "Las órdenes eliminadas no se borran de la base de datos: quedan aquí hasta que las "
        "restaure."
    ),
    "Select an order from the trash.": "Seleccione una orden de la papelera.",
    "The order could not be restored. Please try again.": (
        "No se pudo restaurar. Intente de nuevo."
    ),
    "Edit user": "Editar usuario",
    "New user": "Nuevo usuario",
    "As it should appear on documents": "Como debe salir en los documentos",
    "Role": "Rol",
    "The user name cannot be changed once created.": (
        "El nombre de usuario no se puede cambiar una vez creado."
    ),
    "The user could not be saved. Please try again.": (
        "No se pudo guardar el usuario. Intente de nuevo."
    ),
    "Users": "Usuarios",
    "New user…": "Nuevo usuario…",
    "Change password…": "Cambiar contraseña…",
    "Deactivate": "Desactivar",
    "The full name appears in the order history and in the footer of the documents printed by each user.": (
        "El nombre completo es el que aparece en el historial de las órdenes y en el pie de "
        "los documentos que imprime cada usuario."
    ),
    "Active": "Activo",
    "Deactivated": "Desactivado",
    "Never": "Nunca",
    "Activate": "Activar",
    "You cannot deactivate the account you are working with.": (
        "No puede desactivar la cuenta con la que está trabajando."
    ),
    "The status could not be changed. Please try again.": (
        "No se pudo cambiar el estado. Intente de nuevo."
    ),
}

# Diferencias por contexto: la misma palabra significa una cosa en cada pantalla.
OVERRIDES: dict[tuple[str, str], str] = {
    ("PaymentDialog", "Notes"): "Observaciones",
    ("SettingsDialog", "Email"): "Correo",
    ("MainWindow", "Equipment"): "Equipos",
}

EXTRA: dict[str, str] = {
    "Reception receipt": "Comprobante de recepción",
    "Technical report": "Informe técnico",
    "Delivery receipt": "Comprobante de entrega",
    "Full history": "Historial completo",
    "Save as PDF": "Guardar como PDF",
    "Save the document to a PDF file": "Guardar el documento en un archivo PDF",
    "The document was saved to:\n{0}": "El documento se guardó en:\n{0}",
    "The PDF file could not be written.": "No se pudo escribir el archivo PDF.",
    "Page {page} of {pages}": "Página {page} de {pages}",
    "PDF document (*.pdf)": "Documento PDF (*.pdf)",
    "This field is required.": "Campo obligatorio.",
    "The ID number must have 10 digits.": "La cédula debe tener 10 dígitos.",
    "The ID number may only contain digits.": "La cédula solo puede contener números.",
    "Invalid province code (01 to 24, or 30).": (
        "Código de provincia no válido (01 a 24, o 30)."
    ),
    "The third digit must be between 0 and 5 for private individuals.": (
        "El tercer dígito debe estar entre 0 y 5 para personas naturales."
    ),
    "The ID number is not valid (check digit).": (
        "La cédula no es válida (dígito verificador)."
    ),
    "The phone may only contain digits, spaces, +, - and brackets.": (
        "El teléfono solo puede tener números, espacios, +, - y paréntesis."
    ),
    "The phone must have between 7 and 15 digits.": (
        "El teléfono debe tener entre 7 y 15 dígitos."
    ),
    "Invalid email address.": "Correo electrónico no válido.",
    "Select an equipment type from the list.": "Seleccione un tipo de equipo de la lista.",
    "The selected customer no longer exists.": "El cliente seleccionado ya no existe.",
    "Select an existing customer or fill in the new customer details.": (
        "Seleccione un cliente existente o complete los datos de cliente nuevo."
    ),
    "The amount cannot be negative.": "El importe no puede ser negativo.",
    "Invalid amount. Use digits and a decimal point only.": (
        "Importe no válido. Use solo números y punto decimal."
    ),
    "The deposit cannot exceed the total including taxes.": (
        "El anticipo no puede superar el total con impuestos."
    ),
    "The estimated date cannot be earlier than the received date.": (
        "La fecha estimada no puede ser anterior a la fecha de ingreso."
    ),
    "The amount must be greater than zero.": "El importe debe ser mayor que cero.",
    "You cannot refund more than has been paid.": (
        "No se puede reembolsar más de lo pagado."
    ),
    "A deposit was already recorded at reception; this payment will be subtracted on top of that deposit.": (
        "Ya hay un anticipo registrado en la recepción; este pago se restará además de ese "
        "anticipo."
    ),
    "This payment was already voided.": "Este pago ya estaba anulado.",
    "The selected equipment does not belong to this customer.": (
        "El equipo elegido no pertenece a este cliente."
    ),
    "ID, tax ID or identification": "Cédula, RUC o identificación",
    "Values": "Valores",
    "Handed to the customer when the equipment is left: details, physical condition, accessories, photographs, amounts and service conditions.": (
        "Se entrega al cliente cuando deja el equipo: datos, estado físico, accesorios, "
        "fotografías, valores y condiciones del servicio."
    ),
    "Itemised quantities and prices, total, validity, terms and warranty, plus room for the customer's approval.": (
        "Detalle de los conceptos con cantidades y precios, total, validez, términos y "
        "garantía, y espacio para la aprobación del cliente."
    ),
    "Diagnosis, work performed, parts, recommendations, photographs, warranty coverage and warranty terms.": (
        "Diagnóstico, trabajo realizado, repuestos, recomendaciones, fotografías, garantía, "
        "términos y condiciones de la garantía."
    ),
    "Handed over when the equipment is returned: work performed, payments, balance, warranty, terms and declaration of conformity.": (
        "Se entrega al devolver el equipo: trabajo realizado, pagos, saldo, garantía, "
        "términos y declaración de conformidad."
    ),
    "Every status change, note and payment of the order in chronological order.": (
        "Todos los cambios de estado, notas y pagos de la orden en orden cronológico."
    ),
}

MISSING = object()


def main() -> int:
    tree = ET.parse(TS)
    root = tree.getroot()
    missing: list[tuple[str, str]] = []
    filled = 0
    for context in root.findall("context"):
        name = context.findtext("name") or ""
        for message in context.findall("message"):
            source = message.findtext("source")
            translation = message.find("translation")
            if source is None or translation is None:
                continue
            if (translation.text or "").strip():
                continue
            text = OVERRIDES.get((name, source))
            if text is None:
                text = ES.get(source) or EXTRA.get(source) or MISSING  # type: ignore[arg-type]
            if text is MISSING:
                missing.append((name, source))
                continue
            translation.text = text  # type: ignore[assignment]
            filled += 1
    tree.write(TS, encoding="utf-8", xml_declaration=True)
    print(f"Traducidas: {filled}; sin traducir: {len(missing)}")
    for name, source in missing:
        print(f"  [{name}] {source!r}")
    return 0 if not missing else 1


if __name__ == "__main__":
    sys.exit(main())
