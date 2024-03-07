
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
        
        return {"message": f"Nuevo contacto creado con ID: {contact_id}"}
    
    @route('/create_sell_order', methods=['POST'], type='json', auth='user')
    def create_order_sell(self):

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

        return {"message": f"Orden de venta creada con ID: {sale_order.id}, Team ID: {sale_order.team_id.id}"}
    