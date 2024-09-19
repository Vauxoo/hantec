# -*- coding: utf-8 -*-


from odoo import fields, models, api, _
from odoo.exceptions import UserError
from odoo.osv import expression
from odoo.tools.float_utils import float_round


class SaleWarehouse(models.TransientModel):
	_name = "sale.warehouse"
	_description = "Sale Warehouse"

	product_id = fields.Many2one('product.product',string="Product")
	stock_line = fields.One2many('sale.warehouse.line','sale_stock_id',string="Stock Line")

	@api.model
	def default_get(self,fields):
		res = super(SaleWarehouse, self).default_get(fields)
		order_line_id = self.env['sale.order.line'].browse(self._context.get('active_id'))
		product_id = order_line_id.product_id
		company_id = self.env.user.company_id
		lines = []
		if company_id.stock_type == 'warehouse_wise':
			warehouse_ids = self.env['stock.warehouse'].search([])
			for warehouse in warehouse_ids:
				res = self._compute_quantities_dict(product_id,
													lot_id = self._context.get('lot_id'),
													warehouse_id = warehouse.id, 
													from_date = self._context.get('from_date'),
													to_date = self._context.get('to_date'))
				qty_available     = res.get(product_id.id).get('qty_available') or 0.0
				incoming_qty      = res.get(product_id.id).get('incoming_qty') or 0.0
				outgoing_qty      = res.get(product_id.id).get('outgoing_qty') or 0.0
				virtual_available = res.get(product_id.id).get('virtual_available') or 0.0
				lines.append([0, 0, {
					'warehouse_id' : warehouse.id,
					'on_hand' : product_id.qty_available,
					'available_qty' : qty_available,
				}])
		else:
			location_ids = self.env['stock.location'].search([('usage','=','internal')])
			for location in location_ids:
				res = self._compute_quantities_dict(product_id,
													lot_id = self._context.get('lot_id'),
													location_id = location.id,  
													from_date = self._context.get('from_date'),
													to_date = self._context.get('to_date'))
				qty_available     = res.get(product_id.id).get('qty_available') or 0.0
				incoming_qty      = res.get(product_id.id).get('incoming_qty') or 0.0
				outgoing_qty      = res.get(product_id.id).get('outgoing_qty') or 0.0
				virtual_available = res.get(product_id.id).get('virtual_available') or 0.0
				lines.append([0, 0, {
					'location_id'  : location.id,
					'warehouse_id' : location.warehouse_id.id,
					'on_hand' : product_id.qty_available,
					'available_qty' : qty_available,
				}])
		res.update({
			'product_id': product_id.id,
			'stock_line': lines
		})
		return res

	def _get_domain_locations(self, location_id, warehouse_id):
		'''
		Parses the context and returns a list of location_ids based on it.
		It will return all stock locations when no parameters are given
		Possible parameters are shop, warehouse, location, compute_child
		'''
		Warehouse = self.env['stock.warehouse']

		def _search_ids(model, values):
			ids = set()
			domain = []
			for item in values:
				if isinstance(item, int):
					ids.add(item)
				else:
					domain = expression.OR([[(self.env[model]._rec_name, 'ilike', item)], domain])
			if domain:
				ids |= set(self.env[model].search(domain).ids)
			return ids

		location = location_id
		if location and not isinstance(location, list):
			location = [location]
		warehouse = warehouse_id
		if warehouse and not isinstance(warehouse, list):
			warehouse = [warehouse]
		# filter by location and/or warehouse
		if warehouse:
			w_ids = set(Warehouse.browse(_search_ids('stock.warehouse', warehouse)).mapped('view_location_id').ids)
			if location:
				l_ids = _search_ids('stock.location', location)
				location_ids = w_ids & l_ids
			else:
				location_ids = w_ids
		else:
			if location:
				location_ids = _search_ids('stock.location', location)
			else:
				location_ids = set(Warehouse.search([]).mapped('view_location_id').ids)

		return self._get_domain_locations_new(location_ids)


	def _get_domain_locations_new(self, location_ids):
		locations = self.env['stock.location'].browse(location_ids)
		loc_domain, dest_loc_domain = [], []
		for location in locations:
			loc_domain = loc_domain and ['|'] + loc_domain or loc_domain
			loc_domain.append(('location_id.parent_path', '=like', location.parent_path + '%'))
			dest_loc_domain = dest_loc_domain and ['|'] + dest_loc_domain or dest_loc_domain
			dest_loc_domain.append(('location_dest_id.parent_path', '=like', location.parent_path + '%'))

		return (
			loc_domain,
			dest_loc_domain + ['!'] + loc_domain if loc_domain else dest_loc_domain,
			loc_domain + ['!'] + dest_loc_domain if dest_loc_domain else loc_domain
		)


	def _compute_quantities_dict(self, product_id, lot_id=False, owner_id=False, package_id=False, location_id=False , warehouse_id=False, from_date=False, to_date=False):
		domain_quant_loc, domain_move_in_loc, domain_move_out_loc = self._get_domain_locations(location_id, warehouse_id)
		domain_quant = [('product_id', 'in', [product_id.id])] + domain_quant_loc
		dates_in_the_past = False
		# only to_date as to_date will correspond to qty_available
		to_date = fields.Datetime.to_datetime(to_date)
		if to_date and to_date < fields.Datetime.now():
			dates_in_the_past = True

		domain_move_in = [('product_id', 'in', [product_id.id])] + domain_move_in_loc
		domain_move_out = [('product_id', 'in', [product_id.id])] + domain_move_out_loc
		if lot_id is not None:
			domain_quant += [('lot_id', '=', lot_id)]
		if owner_id is not None:
			domain_quant += [('owner_id', '=', owner_id)]
			domain_move_in += [('restrict_partner_id', '=', owner_id)]
			domain_move_out += [('restrict_partner_id', '=', owner_id)]
		if package_id is not None:
			domain_quant += [('package_id', '=', package_id)]
		if dates_in_the_past:
			domain_move_in_done = list(domain_move_in)
			domain_move_out_done = list(domain_move_out)
		if from_date:
			domain_move_in += [('date', '>=', from_date)]
			domain_move_out += [('date', '>=', from_date)]
		if to_date:
			domain_move_in += [('date', '<=', to_date)]
			domain_move_out += [('date', '<=', to_date)]

		Move = self.env['stock.move']
		Quant = self.env['stock.quant']
		domain_move_in_todo = [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available'))] + domain_move_in
		domain_move_out_todo = [('state', 'in', ('waiting', 'confirmed', 'assigned', 'partially_available'))] + domain_move_out
		moves_in_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in_todo, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
		moves_out_res = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out_todo, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
		quants_res = dict((item['product_id'][0], item['quantity']) for item in Quant.read_group(domain_quant, ['product_id', 'quantity'], ['product_id'], orderby='id'))
		if dates_in_the_past:
			# Calculate the moves that were done before now to calculate back in time (as most questions will be recent ones)
			domain_move_in_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_in_done
			domain_move_out_done = [('state', '=', 'done'), ('date', '>', to_date)] + domain_move_out_done
			moves_in_res_past = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_in_done, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
			moves_out_res_past = dict((item['product_id'][0], item['product_qty']) for item in Move.read_group(domain_move_out_done, ['product_id', 'product_qty'], ['product_id'], orderby='id'))
		res = dict()
		for product in [product_id.id]:
			product_id = product
			product = self.env['product.product'].browse(product_id)
			rounding = product.uom_id.rounding
			res[product_id] = {}
			if dates_in_the_past:
				qty_available = quants_res.get(product_id, 0.0) - moves_in_res_past.get(product_id, 0.0) + moves_out_res_past.get(product_id, 0.0)
			else:
				qty_available = quants_res.get(product_id, 0.0)
			res[product_id]['qty_available'] = float_round(qty_available, precision_rounding=rounding)
			res[product_id]['incoming_qty'] = float_round(moves_in_res.get(product_id, 0.0), precision_rounding=rounding)
			res[product_id]['outgoing_qty'] = float_round(moves_out_res.get(product_id, 0.0), precision_rounding=rounding)
			res[product_id]['virtual_available'] = float_round(
				qty_available + res[product_id]['incoming_qty'] - res[product_id]['outgoing_qty'],
				precision_rounding=rounding)
		return res


class SaleWarehouseLine(models.TransientModel):
	_name = "sale.warehouse.line"
	_description = "Sale Warehouse"


	warehouse_id = fields.Many2one('stock.warehouse',string="Warehouse")
	location_id = fields.Many2one('stock.location',string="Location")
	on_hand = fields.Float('On Hand Qty')
	available_qty = fields.Float('Available Qty')
	sale_stock_id = fields.Many2one('sale.warehouse',string="Sale Stock")
