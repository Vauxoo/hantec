# -*- coding: utf-8 -*-

from odoo import api, fields, models,_
from odoo.exceptions import UserError, ValidationError
from datetime import datetime

class ResCompany(models.Model):
    _inherit = "res.company"

    stock_type = fields.Selection([('warehouse_wise','Warehouse Wise'),('location_wise','Location Wise')],string="Stock Type")

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    stock_type = fields.Selection([('warehouse_wise','Warehouse Wise'),('location_wise','Location Wise')],string="Stock Type", related="company_id.stock_type" ,readonly=False, required="True")

class SaleOrderLineIn(models.Model):
    _inherit = "sale.order.line"


    def show_product_stock(self):
        action = self.env["ir.actions.actions"]._for_xml_id('sale_product_stock_app.action_view_add_sale_stock_warehouser')
        action['context'] = self._context
        return action