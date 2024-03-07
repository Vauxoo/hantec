
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