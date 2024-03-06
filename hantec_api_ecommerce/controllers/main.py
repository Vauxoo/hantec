from odoo.http import request, Controller, route
import logging, re

logger = logging.getLogger(__name__)


class MainController(Controller):
    @route("/create_contact", methods=["POST"], type="json", auth="user")
    def create_contact(self):
        """
        Combines the logic of searching and creating contacts based on email, phone, or store name.

        This function first checks if a contact already exists based on the provided
        email, phone, or store name. If a matching contact is found, it returns the contact ID.
        If no matching contact is found, it creates a new contact with the provided data.

        JSON request body:
            - email (str, optional): The email of the contact.
            - phone (str, optional): The phone number of the contact.
            - store_name (str, optional): The store name associated with the contact.
            - partner_id (int, optional): The parent ID for the contact.
            - contact_data (dict, optional): Additional contact data.

        JSON response:
            - message (str): A message indicating whether a contact was found or created.
            - contact_id (int): The ID of the found or created contact.

        Returns:
            dict: A dictionary with a message and the contact ID.

        """
        env = request.env
        data = request.jsonrequest
        email = data.get("email")
        phone = data.get("phone")
        store_name = data.get("store_name")
        partner_id = data.get("partner_id")
        contact_data = data.get("contact_data", {})

        if email or phone:
            email_pattern = r"^([a-z0-9!#$%&'*+/=?^_`{|}~-]+(?:\.[a-z0-9!#$%&'*+/=?^_`{|}~-]+)*)"  # Email pattern to get the value before @
            email_prefix = re.match(email_pattern, email).group() if email else None
            phone_suffix = phone[len(phone) - 5 :] if phone else None

            domain = []
            if email_prefix:
                domain.append(("email", "ilike", f"{email_prefix}%"))
            if phone_suffix:
                domain.append(("phone", "ilike", f"%{phone_suffix}"))

            existing_contact = env["res.partner"].search(domain, limit=1)

            if existing_contact:
                logger.info("Contact found with ID %s", existing_contact.id)
                return {
                    "message": f"Contact found with ID: {existing_contact.id}.",
                    "contact_id": existing_contact.id,
                }

            if "email" not in contact_data and email:
                contact_data["email"] = email
            if "phone" not in contact_data and phone:
                contact_data["phone"] = phone

        if store_name:
            store_name_suffix = store_name[len(store_name) - 4 :]

            domain = [("name", "ilike", f"%{store_name_suffix}")]
            existing_contact = env["res.partner"].search(domain, limit=1)

            if existing_contact:
                logger.info("Contact found with ID %s", existing_contact.id)
                return {
                    "message": f"Contact found with ID: {existing_contact.id}.",
                    "contact_id": existing_contact.id,
                }

            contact_data.update({"type": "other", "parent_id": partner_id})

        new_contact = env["res.partner"].create(contact_data)
        logger.info("New contact created with ID %s", new_contact.id)
        return {
            "message": f"New contact created with ID {new_contact.id}",
            "contact_id": new_contact.id,
        }

    @route("/update_contact", methods=["POST"], type="json", auth="user")
    def update_contact(self):
        """
        Updates a contact with new values.

        This function updates the details of a specified contact using the values
        provided in the JSON request body.

        JSON request body:
            - partner_id (int): The ID of the contact to be updated.
            - update_vals (dict): A dictionary containing the values to be updated.

        JSON response:
            - message (str): A message indicating that the contact has been successfully updated.

        Returns:
            dict: A dictionary with a success message.

        """
        data = request.jsonrequest
        partner_id = data.get("partner_id")  # ID of the contact to be updated
        update_vals = data.get("update_vals")  # Values to update

        # Find the contact by its ID
        partner = request.env["res.partner"].browse(partner_id)

        # Update the contact with the new values
        partner.write(update_vals)

        logger.info("Contact updated with ID %s", partner_id)

        return {"message": f"Contact with ID: {partner_id} successfully updated."}

    @route("/address_invoice", methods=["POST"], type="json", auth="user")
    def create_address_invoice(self):
        """
        Creates or updates the billing address for a given partner.

        This function creates or updates the billing address of a specified partner
        using the details provided in the JSON request body.

        JSON request body:
            - partner_id (int): The ID of the partner.
            - invoice_data (dict): A dictionary containing the billing address details.

        JSON response:
            - message (str): A message indicating that the billing address has been successfully created or updated.
            - invoice_id (int): The ID of the created or updated billing address.

        Returns:
            dict: A dictionary with a success message and the billing address ID.

        """
        env = request.env
        data = request.jsonrequest
        partner_id = data.get("partner_id")
        invoice_data = data.get("invoice_data")

        partner = env["res.partner"].browse(partner_id)

        # Search if a billing address already exists
        invoice_address = env["res.partner"].search(
            [("parent_id", "=", partner_id), ("type", "=", "invoice")], limit=1
        )

        if invoice_address:
            # Update existing billing address
            invoice_address.write(invoice_data)
        else:
            # Add a new billing address
            invoice_data.update({"type": "invoice", "parent_id": partner_id})
            invoice_address = env["res.partner"].create(invoice_data)

        return {
            "message": "Billing address successfully updated/created.",
            "invoice_id": invoice_address.id,
        }

    @route("/delivery_address", methods=["POST"], type="json", auth="user")
    def delivery_address(self):
        """
        Creates or updates the delivery address for a given partner.

        This function creates or updates the delivery address of a specified partner
        using the details provided in the JSON request body.

        JSON request body:
            - partner_id (int): The ID of the partner.
            - address_data (dict): A dictionary containing the address details.
            - only_create (bool, optional): A boolean indicating if only creation should be done,
            omitting the update of an existing address (default is False).

        JSON response:
            - message (str): A message indicating that the delivery address has been successfully created or updated.
            - delivery_address_id (int): The ID of the created or updated delivery address.

        Returns:
            dict: A dictionary with a success message and the delivery address ID.

        """
        env = request.env
        data = request.jsonrequest
        partner_id = data.get("partner_id")
        delivery_data = data.get("address_data")
        only_create = data.get("only_create", False)  # Boolean to omit address update
        partner = env["res.partner"].browse(partner_id)

        # Create or update the delivery address
        delivery_address = env["res.partner"].search(
            [("parent_id", "=", partner_id), ("type", "=", "delivery")], limit=1
        )

        if only_create:
            delivery_address = False

        if delivery_address:
            # Update existing delivery address
            delivery_address.write(delivery_data)
        else:
            # Add a new delivery address
            delivery_data.update({"type": "delivery", "parent_id": partner_id})
            delivery_address = env["res.partner"].create(delivery_data)

        return {
            "message": "Delivery address successfully updated/created.",
            "delivery_address_id": delivery_address.id,
        }

    @route("/create_sale_order", methods=["POST"], type="json", auth="user")
    def create_sale_order(self):
        """
        Creates a sale order.

        This function creates a sale order using the details provided in the JSON request body.
        The required fields include the customer ID and a list of product lines.

        JSON request body:
            Required fields:
                - partner_id (int): The ID of the customer.
                - product_lines (list of dicts): A list of dictionaries containing product details:
                    - product_id (int): The ID of the product.
                    - product_qty (float): The quantity of the product.
                    - price_unit (float, optional): The unit price of the product (default is 0).
                    - discount (float, optional): The discount on the product (default is 0).
                    - tax_id (int, optional): The tax ID for the product (default is 2).
                - price_shipping (float): The shipping price.

            Optional fields:
                - team_id (int): The ID of the sales team.
                - origin (str): The origin of the order.
                - campaign_id (int): The ID of the marketing campaign.
                - medium_id (int): The ID of the marketing medium.
                - channel_order_reference (str): The reference for the channel order.
                - yuju_carrier_tracking_ref (str): The tracking reference for the carrier.
                - partner_shipping_id (int): The ID of the shipping partner.

        JSON response:
            - message (str): A message indicating that the sale order has been successfully created.
            - sale_order_id (int): The ID of the created sale order.
            - sale_order_name (str): The name of the created sale order.

        Returns:
            dict: A dictionary with a success message, the sale order ID, and the sale order name.

        """
        # ID of client (partner_id) y list of products (product_lines)
        required_fields = [
            "partner_id",
            "product_lines",
            "price_shipping",
        ]  # product_lines is a dictionary list with 'product_id' and 'product_qty'
        optional_fields = [
            "team_id",
            "origin",
            "campaign_id",
            "medium_id",
            "channel_order_reference",
            "yuju_carrier_tracking_ref",
            "partner_shipping_id",
        ]
        sale_order_data = {
            field: request.jsonrequest.get(field)
            for field in required_fields + optional_fields
            if request.jsonrequest.get(field)
        }

        order_line = [
            (
                0,
                0,
                {
                    "product_id": line["product_id"],
                    "product_uom_qty": line["product_qty"],
                    "price_unit": line.get("price_unit", 0),
                    "discount": line.get("discount", 0),
                    "tax_id": [(6, 0, [line.get("tax_id", 2)])],
                },
            )
            for line in sale_order_data["product_lines"]
        ]

        sale_order_vals = {
            "partner_id": sale_order_data["partner_id"],
            "order_line": order_line,
        }

        # Add optional values
        for field in optional_fields:
            if field in sale_order_data:
                sale_order_vals[field] = sale_order_data[field]

        # Create sale order
        sale_order = request.env["sale.order"].create(sale_order_vals)

        logger.info(
            "Sale order created with ID %s and Team ID %s",
            sale_order.id,
            sale_order.team_id.id,
        )

        return {
            "message": f"Sale order created with ID: {sale_order.id}, Team ID: {sale_order.team_id.id}",
            "sale_order_id": sale_order.id,
            "sale_order_name": sale_order.name,
        }

    @route("/update_sale_order", methods=["POST"], type="json", auth="user")
    def update_sale_order(self):
        """
        Updates a sale order with a tracking number.

        This function updates the tracking number of a specified sale order using the details
        provided in the JSON request body.

        JSON request body:
            - sale_order_id (int): The ID of the sale order to be updated.
            - tracking_number (str): The tracking number to be assigned to the sale order.

        JSON response:
            - message (str): A message indicating that the sale order has been successfully updated.

        Returns:
            dict: A dictionary with a success message.

        """
        sale_order_id = request.jsonrequest.get("sale_order_id")
        tracking_number = request.jsonrequest.get("tracking_number")

        # Find the sale order by its ID
        sale_order = request.env["sale.order"].browse(sale_order_id)
        sale_order.update({"yuju_carrier_tracking_ref": tracking_number})

        return {
            "message": f"The order with ID: {sale_order_id} has been successfully updated."
        }

    @route(
        '/invoice_sale_order/<model("sale.order"):order>',
        methods=["POST"],
        type="json",
        auth="user",
    )
    def invoice_sale_order(self, order=False):
        """
        Creates an invoice for a sale order.

        This function creates an invoice for a specified sale order using the details
        provided in the JSON request body.

        URL parameter:
            - order (sale.order): The sale order model instance.

        JSON request body:
            - code_usage (str): The code usage for the invoice (optional, default is "G01").

        JSON response:
            - message (str): A message indicating that the invoice has been successfully created.
            - list_invoices (list): A list of dictionaries containing the name and date of the created invoices.

        Returns:
            dict: A dictionary with a success message and a list of created invoices.

        """
        data = request.jsonrequest
        context = {
            "active_model": "sale.order",
            "active_ids": [order.id],
            "active_id": order.id,
        }
        invoice_wizard = (
            request.env["sale.advance.payment.inv"]
            .with_context(**context)
            .create({"advance_payment_method": "delivered"})
        )

        # Create invoice
        invoice_wizard.create_invoices()
        invoices = order.invoice_ids

        for invoice in invoices:
            invoice.write({"l10n_mx_edi_usage": data.get("code_usage", "G01")})

        # Confirm invoice
        invoices.action_post()

        return {
            "message": "Invoice created",
            "list_invoices": invoices.read(["name", "date"]),
        }

    @route(
        '/register_payment_invoice/<model("account.move"):invoice>',
        methods=["POST"],
        type="json",
        auth="user",
    )
    def register_payment(self, invoice=False):
        """
        Registers a payment for an invoice.

        This function registers a payment for a specified invoice using the details
        provided in the JSON request body.

        URL parameter:
            - invoice (account.move): The invoice model instance.

        JSON request body:
            - amount (float): The amount to be paid.
            - journal_id (int): The ID of the payment journal.
            - payment_method_id (int): The ID of the payment method.

        JSON response:
            - success (str): A message indicating that the payment has been successfully registered.

        Returns:
            dict: A dictionary with a success message.

        """
        data = request.jsonrequest
        amount = data.get("amount")
        journal_id = data.get("journal_id")
        payment_method_id = data.get("payment_method_id")

        register_payment_wizard = request.env["account.payment.register"].with_context(
            active_model="account.move", active_ids=[invoice.id]
        )

        wizard = register_payment_wizard.create(
            {
                "amount": amount,
                "journal_id": journal_id,
                "l10n_mx_edi_payment_method_id": payment_method_id,
                "communication": "Payment for invoice %s" % invoice.name,
            }
        )

        # Register the payment
        wizard.action_create_payments()

        return {"success": "The payment has been successfully registered."}

    @route(
        '/get_shipping_info/<model("sale.order"):order>',
        methods=["GET"],
        type="json",
        auth="user",
    )
    def get_shipping_info(self, order=False):
        """
        Retrieves shipping information for a given sale order.

        This function gathers shipping information related to the specified sale order,
        including delivery address details and shipping records.

        URL parameter:
            - order (sale.order): The sale order model instance.

        JSON response:
            - message (str): A message indicating that the shipping data has been successfully retrieved.
            - shipping_data (list): A list of dictionaries containing shipping information.

        Returns:
            dict: A dictionary with a success message and the shipping data.

        """
        # Delivery address data
        shipping_address = order.partner_shipping_id
        address_data = {
            "name": shipping_address.name,
            "phone": shipping_address.phone,
            "email": shipping_address.email,
            "street": shipping_address.street,
            "street2": shipping_address.street2,
            "city": shipping_address.city,
            "state": (
                shipping_address.state_id.name if shipping_address.state_id.name else ""
            ),
            "zip": shipping_address.zip,
            "country": (
                shipping_address.country_id.name if shipping_address.country_id else ""
            ),
        }

        # Get related shipping records
        pickings = order.picking_ids

        # Prepare shipping data for the response
        shipping_data = []
        last_picking = None
        for picking in pickings:
            lines_data = [
                {
                    "product": line.product_id.name,
                    "quantity": line.product_uom_qty,
                    "done": line.quantity_done,
                    "name": line.name,
                }
                for line in picking.move_lines
            ]

            shipping_info = {
                "name": picking.name,
                "scheduled_date": picking.scheduled_date,
                "state": picking.state,
                "carrier": (
                    picking.carrier_id.name if picking.carrier_id else "Not defined"
                ),
                "tracking_reference": picking.carrier_tracking_ref,
                "lines": lines_data,
                "address_data": address_data,
            }
            shipping_data.append(shipping_info)
            last_picking = picking

        if last_picking:
            shipping_data.append(
                {
                    "sales_team": order.team_id.id,
                    "market_place_reference": order.channel_order_reference,
                    "sale_order_name": order.name,
                    "picking_id": last_picking.id,
                    "picking_name": last_picking.name,
                }
            )

        return {"message": "Shipping data retrieved", "shipping_data": shipping_data}

    @route(
        "/download_invoice/<int:invoice_id>", methods=["GET"], type="http", auth="user"
    )
    def download_invoice(self, invoice_id):
        """
        Downloads an invoice as a PDF.

        This function generates and downloads a PDF file for the invoice identified by its ID.

        URL parameter:
            - invoice_id (int): The ID of the invoice to be downloaded.

        HTTP response:
            - Content-Type: application/pdf
            - Content-Length: The length of the PDF content

        Returns:
            response: An HTTP response with the PDF content of the invoice.

        """
        # Find the invoice
        invoice = request.env["account.move"].browse(invoice_id)

        # Generate the PDF
        pdf_content, _ = request.env.ref("account.account_invoices")._render_qweb_pdf(
            [invoice_id]
        )
        http_headers = [
            ("Content-Type", "application/pdf"),
            ("Content-Length", len(pdf_content)),
        ]
        return request.make_response(pdf_content, headers=http_headers)

    @route(
        "/stamp_invoice/<int:invoice_id>", methods=["POST"], auth="user", type="json"
    )
    def stamp_invoice(self, invoice_id=None):
        """
        Stamps an invoice.

        This function attempts to stamp an invoice identified by its ID. If the invoice
        is already stamped, it returns the UUID of the stamped invoice. Otherwise, it
        tries to stamp the invoice and returns the result.

        URL parameter:
            - invoice_id (int): The ID of the invoice to be stamped.

        JSON response:
            - If the invoice is already stamped:
                - message (str): A message indicating that the invoice is already stamped.
                - UUID (str): The UUID of the stamped invoice.
            - If the stamping process is successful:
                - success (str): A message indicating that the invoice has been successfully stamped.
                - UUID (str): The UUID of the stamped invoice.
            - If the stamping process fails:
                - error (str): A message indicating that the stamping process failed.
                - details (str): The error message from the stamping process.

        Returns:
            dict: A dictionary with the result of the stamping process.

        """
        # Find the invoice by its ID
        invoice = request.env["account.move"].browse(invoice_id)

        # Check if the invoice is already stamped
        if invoice.l10n_mx_edi_cfdi_uuid:
            return {
                "message": "The invoice is already stamped.",
                "UUID": invoice.l10n_mx_edi_cfdi_uuid,
            }

        # Attempt the stamping process
        invoice.action_process_edi_web_services()

        # Check again if the invoice was successfully stamped
        if invoice.l10n_mx_edi_cfdi_uuid:
            return {
                "success": "The invoice has been successfully stamped.",
                "UUID": invoice.l10n_mx_edi_cfdi_uuid,
            }

        # If stamping failed, get the error messages
        error_message = invoice.edi_error_message
        return {
            "error": "The invoice stamping failed.",
            "details": error_message,
        }

    @route(
        "/send_invoice_by_email/<int:invoice_id>",
        type="json",
        auth="user",
        methods=["POST"],
    )
    def send_invoice_by_email(self, invoice_id=False):
        """
        Sends an invoice by email.

        This function sends an invoice identified by its ID via email, using the
        invoice sending wizard in Odoo.

        URL parameter:
            - invoice_id (int): The ID of the invoice to be sent.

        JSON response:
            - success (str): A message indicating that the invoice has been successfully sent.

        Returns:
            dict: A dictionary with a success message.

        """
        invoice = request.env["account.move"].browse(invoice_id)
        action = invoice.action_invoice_sent()
        action_context = action["context"]
        invoice_send_wizard = (
            request.env["account.invoice.send"]
            .with_context(action_context, active_ids=[invoice.id])
            .create({"is_print": False})
        )

        # Send the invoice by email
        invoice_send_wizard.send_and_print_action()

        return {"success": "The invoice has been successfully sent."}

    @route("/confirm_sale_order", methods=["POST"], type="json", auth="user")
    def confirm_sale_order(self):
        """
        Confirms a sale order.

        This function confirms a sale order identified by its ID, using the details
        provided in the JSON request body.

        JSON request body:
            - sale_order_id (int): The ID of the sale order to be confirmed.

        JSON response:
            - message (str): A confirmation message indicating the action performed.

        Returns:
            dict: A dictionary with a confirmation message.

        """
        data = request.jsonrequest
        sale_order_id = data.get("sale_order_id")

        # Find the sale order by its ID
        sale_order = request.env["sale.order"].browse(sale_order_id)

        # Confirm the sale order
        sale_order.action_confirm()
        logger.info("Sale order confirmed with ID %s", sale_order_id)

        return {
            "message": f"Sale order with ID: {sale_order_id} successfully confirmed."
        }

    @route("/create_schedule_activity", methods=["POST"], type="json", auth="user")
    def create_schedule_activity(self):
        """
        Creates a scheduled activity associated with an existing sale order.

        This function creates a scheduled activity in Odoo related to a specific sale order,
        using the details provided in the JSON request body.

        JSON request body:
            - sale_order_id (int): ID of the existing sale order.
            - activity_type_id (int): ID of the activity type.
            - summary (str, optional): Summary text of the activity.
            - date_deadline (str): Deadline date for the activity in 'YYYY-MM-DD' format.
            - note (str, optional): Note for the activity.
            - user_id (int, optional): ID of the user assigned to the activity. If not provided, the current user's ID is used.

        JSON response:
            - message (str): A confirmation message with the ID of the scheduled activity and the sale order ID.

        Returns:
            dict: A dictionary with a confirmation message.
        """
        data = request.jsonrequest
        sale_order_id = data.get("sale_order_id")  # ID of the existing sale order
        activity_type_id = data.get("activity_type_id")  # ID of the activity type
        summary = data.get("summary", "")  # Summary text of the activity (optional)
        date_deadline = data.get("date_deadline")  # Deadline date for the activity
        note = data.get("note", "")  # Note for the activity (optional)
        user_id = data.get("user_id", request.env.uid)  # User assigned to the activity

        # Create the scheduled activity
        activity = request.env["mail.activity"].create(
            {
                "activity_type_id": activity_type_id,
                "note": note,
                "date_deadline": date_deadline,
                "res_model_id": request.env["ir.model"]._get("sale.order").id,
                "res_id": sale_order_id,
                "user_id": user_id,
                "summary": summary,
            }
        )
        logger.info(
            "Scheduled activity created with ID %s for sale order %s",
            activity.id,
            sale_order_id,
        )

        return {
            "message": f"Scheduled activity created with ID: {activity.id} for sale order {sale_order_id}."
        }

    @route(
        "/create_schedule_activity_invoice", methods=["POST"], type="json", auth="user"
    )
    def create_schedule_activity_invoice(self):
        """
        Creates a scheduled activity associated with an existing invoice.

        This function creates a scheduled activity in Odoo related to a specific invoice,
        using the details provided in the JSON request body.

        JSON request body:
            - invoice_id (int): ID of the existing invoice.
            - activity_type_id (int): ID of the activity type.
            - summary (str, optional): Summary text of the activity.
            - date_deadline (str): Deadline date for the activity in 'YYYY-MM-DD' format.
            - note (str, optional): Note for the activity.
            - user_id (int, optional): ID of the user assigned to the activity. If not provided, the current user's ID is used.

        JSON response:
            - message (str): Confirmation message with the ID of the scheduled activity and the invoice ID.

        Returns:
            dict: Dictionary with a confirmation message.
        """
        data = request.jsonrequest
        invoice_id = data.get("invoice_id")  # ID of the existing invoice
        activity_type_id = data.get("activity_type_id")  # ID of the activity type
        summary = data.get("summary", "")  # Summary text of the activity (optional)
        date_deadline = data.get("date_deadline")  # Deadline date for the activity
        note = data.get("note", "")  # Note for the activity (optional)
        user_id = data.get("user_id", request.env.uid)  # User assigned to the activity

        # Create the scheduled activity
        activity = request.env["mail.activity"].create(
            {
                "activity_type_id": activity_type_id,
                "note": note,
                "date_deadline": date_deadline,
                "res_model_id": request.env["ir.model"]._get("account.move").id,
                "res_id": invoice_id,
                "user_id": user_id,
                "summary": summary,
            }
        )
        logger.info(
            "Scheduled activity created with ID %s for invoice %s",
            activity.id,
            invoice_id,
        )

        return {
            "message": f"Scheduled activity created with ID: {activity.id} for invoice {invoice_id}."
        }

    @route("/send_message_sale_order", methods=["POST"], type="json", auth="user")
    def send_message_sale_order(self):
        """
        Sends a message to a specific sale order.

        This function posts a message to the chatter of a sale order identified by its ID,
        using the message body provided in the JSON request body.

        JSON request body:
            - sale_order_id (int): The ID of the sale order.
            - message_body (str): The content of the message to be posted.

        JSON response:
            - message (str): A confirmation message indicating the action performed.

        Returns:
            dict: A dictionary with a confirmation message.

        """
        data = request.jsonrequest
        sale_order_id = data.get("sale_order_id")
        message_body = data.get("message_body")

        # Find the sale order by its ID
        sale_order = request.env["sale.order"].browse(sale_order_id)

        # Post the message in the sale order chatter
        sale_order.message_post(body=message_body)
        logger.info("Message posted in sale order with ID %s", sale_order_id)

        return {
            "message": f"Message successfully posted in sale order with ID: {sale_order_id}."
        }

    @route("/get_inventory", methods=["GET"], type="json", auth="user")
    def get_inventory(self):
        """
        Retrieves the inventory details for all products with a SKU.

        This function searches for all products in the Odoo database that have a SKU
        (default_code not null) and returns their inventory details in a JSON response.

        JSON response:
            - message (str): A message indicating the action performed.
            - inventory_data (list of dict): A list of dictionaries containing the inventory details for each product, including:
                - name (str): The name of the product.
                - default_code (str): The SKU of the product.
                - qty_available (float): The quantity of the product available.
                - virtual_available (float): The virtual quantity of the product available.

        Returns:
            dict: A dictionary with a message and the inventory details of the products.
        """
        products = request.env["product.product"].search(
            [("default_code", "!=", False)]
        )

        product_fields = ["name", "default_code", "qty_available", "virtual_available"]
        inventory_list = products.read(product_fields)

        return {
            "message": "Inventory data retrieved",
            "inventory_data": inventory_list,
        }

    @route("/get_inventory_by_sku", methods=["POST"], type="json", auth="user")
    def get_inventory_by_sku(self):
        """
        Retrieves the inventory details for a product based on its SKU.

        This function searches for a product in the Odoo database using the provided SKU
        and returns the inventory details in a JSON response.

        JSON request body:
            - sku (str): The SKU of the product to search for.

        JSON response:
            - message (str): A message indicating the action performed.
            - inventory_data (list of dict): A list of dictionaries containing the product's inventory details, including:
                - name (str): The name of the product.
                - default_code (str): The SKU of the product.
                - qty_available (float): The quantity of the product available.
                - virtual_available (float): The virtual quantity of the product available.

        Returns:
            dict: A dictionary with a message and the inventory details of the product.
        """
        sku = request.jsonrequest.get("sku")
        product = request.env["product.product"].search([("default_code", "=", sku)])
        product_fields = ["name", "default_code", "qty_available", "virtual_available"]
        data_product = product.read(product_fields)

        return {
            "message": "Inventory data retrieved",
            "inventory_data": data_product,
        }

    @route("/get_states_mexico", methods=["GET"], type="http", auth="user")
    def get_states_mexico(self):
        """
        Retrieves the list of states in Mexico.

        This function retrieves the list of states associated with Mexico in the Odoo database
        and returns them in a JSON response.

        JSON response:
            - message (str): A message indicating the action performed.
            - states_list (list of dict): A list of dictionaries containing the names of the states.

        Returns:
            dict: A dictionary with a message and the list of states.
        """
        env = request.env
        mexico = env.ref("base.mx")
        states = mexico.state_ids
        states_list = states.read(["name"])

        return {"message": "List states from Mexico", "states_list": states_list}
