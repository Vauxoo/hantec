
from odoo.http import request, Response, Controller, route

import logging
logger = logging.getLogger(__name__)


class MainController(Controller):
    @route('/create_contact', methods=['POST'], type='json', auth='user' )
    def create_contact(self):
        
        # Lista de todos los campos posibles
        # TODO: Revisar los campos
        all_fields = [
            'company_type', 'name', 'phone', 'street_number', 'street_number2',
            'email', 'street', 'street2', 'city', 'zip', 'state_id', 'country_id',
            'vat', 'l10n_mx_edi_curp', 'website', 'lang', 'category_id', 'l10n_mx_edi_fiscal_regime', 'parent_id'
        ]

        # Construir el diccionario contact_data con solo los campos enviados en el JSON
        contact_data = {field: request.jsonrequest.get(field) for field in all_fields if request.jsonrequest.get(field) is not None}

        # Si category_id está presente, convertirlo en una lista
        if 'category_id' in contact_data and not isinstance(contact_data['category_id'], list):
            contact_data['category_id'] = [contact_data['category_id']]
        
        contact_id = request.env['res.partner'].create(contact_data)

        # Utilizar logger en lugar de print
        logger.info("Nuevo contacto creado con ID %s", contact_id)
        
        return {"message": f"Nuevo contacto creado con ID: {contact_id}", "contact_id": contact_id}
    
    @route('/update_contact', methods=['POST'], type='json', auth='user')
    def update_contact(self):

        data = request.jsonrequest
        partner_id = data.get('partner_id')  # ID del contacto a actualizar
        update_vals = data.get('update_vals')  # Valores a actualizar

        # Encontrar el contacto por su ID
        partner = request.env['res.partner'].browse(partner_id)

        # Actualizar el contacto con los nuevos valores
        partner.write(update_vals)

        logger.info("Contacto actualizado con ID %s", partner_id)

        return {"message": f"Contacto con ID: {partner_id} actualizado exitosamente."}
    
    @route('/manage_contact', methods=['POST'], type='json', auth='user')
    def manage_contact(self):
        
        data = request.jsonrequest
        email = data.get('email')
        phone = data.get('phone')
        contact_data = data.get('contact_data', {})  # Datos del contacto a actualizar/crear

        # Verificar si ya existe un contacto con el mismo correo electrónico o número de celular
        domain = ['|', ('email', '=', email), ('mobile', '=', phone)]
        existing_contact = request.env['res.partner'].search(domain, limit=1)

        for key, value in contact_data.items():
            if isinstance(value, str):
                if key == 'lang' or key == 'company_type':
                    pass
                else:
                    contact_data[key] = value.title()  # Convierte la primera letra de cada palabra a mayúscula

        if existing_contact:
            # Actualizar el contacto existente si se encontró
            existing_contact.write(contact_data)
            logger.info("Contacto actualizado con ID %s", existing_contact.id)
            return {"message": f"Contacto actualizado con ID: {existing_contact.id}.", "contact_id": existing_contact.id}
        else:
            # Crear un nuevo contacto si no se encontró ninguno existente
            if 'email' not in contact_data:
                contact_data['email'] = email
            if 'phone' not in contact_data and phone:  # Solo añadir el teléfono si se proporcionó
                contact_data['phone'] = phone
            new_contact = request.env['res.partner'].create(contact_data)
            logger.info("Nuevo contacto creado con ID %s", new_contact.id)
            return {"message": f"Nuevo contacto creado con ID: {new_contact.id}.", "contact_id": new_contact.id}
    
    @route('/create_sale_order', methods=['POST'], type='json', auth='user')
    def create_sale_order(self):

        # id del cliente (partner_id) y lista de productos (product_lines)
        required_fields = ['partner_id', 'product_lines']  # product_lines es una lista de diccionarios con 'product_id' y 'product_qty'
        optional_fields = ['team_id']
        sale_order_data = {field: request.jsonrequest.get(field) for field in required_fields + optional_fields if request.jsonrequest.get(field)}

        sale_order_vals = {
            'partner_id': sale_order_data['partner_id'],
            'order_line': [(0, 0, {'product_id': line['product_id'], 'product_uom_qty': line['product_qty']}) for line in sale_order_data['product_lines']]
        }
        
        if 'team_id' in sale_order_data:
            sale_order_vals['team_id'] = sale_order_data['team_id']

        # Crear la orden de venta
        sale_order = request.env['sale.order'].create(sale_order_vals)

        logger.info("Orden de venta creada con ID %s y Team ID %s", sale_order.id, sale_order.team_id.id)

        return {"message": f"Orden de venta creada con ID: {sale_order.id}, Team ID: {sale_order.team_id.id}", "sale_order_id": sale_order.team_id.id}
        
    @route('/confirm_sale_order', methods=['POST'], type='json', auth='user')
    def confirm_sale_order(self):
        
        data = request.jsonrequest
        sale_order_id = data.get('sale_order_id')

        # Encontrar la orden de venta por su ID
        sale_order = request.env['sale.order'].browse(sale_order_id)

        # Confirmar la orden de venta
        sale_order.action_confirm()

        logger.info("Orden de venta confirmada con ID %s", sale_order_id)

        return {"message": f"Orden de venta con ID: {sale_order_id} confirmada exitosamente."}
    
    @route('/create_schedule_activity', methods=['POST'], type='json', auth='user')
    def create_schedule_activity(self):

        data = request.jsonrequest
        sale_order_id = data.get('sale_order_id')  # ID de la orden de venta existente
        activity_type_id = data.get('activity_type_id')  # ID del tipo de actividad
        summary = data.get('summary', '') # Texto resumido de la actividad (opcional)
        date_deadline = data.get('date_deadline')  # Fecha límite para la actividad
        note = data.get('note', '')  # Nota de la actividad (opcional)
        user_id = data.get('user_id', request.env.uid)  # Usuario asignado a la actividad

        # Crear la actividad programada
        activity = request.env['mail.activity'].create({
            'activity_type_id': activity_type_id,
            'note': note,
            'date_deadline': date_deadline,
            'res_model_id': request.env['ir.model']._get('sale.order').id,
            'res_id': sale_order_id,
            'user_id': user_id,
            'summary': summary
        })

        logger.info("Actividad programada creada con ID %s para la orden de venta %s", activity.id, sale_order_id)

        return {"message": f"Actividad programada creada con ID: {activity.id} para la orden de venta {sale_order_id}."}
    
    @route('/send_message_sale_order', methods=['POST'], type='json', auth='user')
    def send_message_sale_order(self):
        data = request.jsonrequest
        sale_order_id = data.get('sale_order_id')
        message_body = data.get('message_body')

        # Encontrar la orden de venta por su ID
        sale_order = request.env['sale.order'].browse(sale_order_id)

        # Verificar si la orden de venta existe
        if not sale_order.exists():
            return {"error": f"No se encontró la orden de venta con ID {sale_order_id}."}

        # Publicar el mensaje en el chat de la orden de venta
        sale_order.message_post(body=message_body)

        logger.info("Mensaje publicado en la orden de venta con ID %s", sale_order_id)

        return {"message": f"Mensaje publicado exitosamente en la orden de venta con ID: {sale_order_id}."}