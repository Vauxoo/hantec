# -*- coding: utf-8 -*-
{
    'name': 'Stock Details on Sales Order Line',
    "author": "Edge Technologies",
    'version': '15.0.1.1',
    'live_test_url': "https://youtu.be/gBVrz56cIQU",
    "images":['static/description/main_screenshot.png'],
    'summary':'Sales product stock details on sales warehouse wise stock details on sale order product stock info on sales order stock info location wise stock information on sales stock information warehouse wise stock info on sale order line stock details on sale stock',
    'description': """
        Sales product stock (warehouse/location wise) information app allow you to show product stock inside sale order.
    """,
    "license" : "OPL-1",
    'depends': ['sale_management','stock'],
    'data': [
        'wizard/sale_warehouse.xml',
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/sale_order.xml',
    ],
    'installable': True,
    'auto_install': False,
    'price': 10,
    'currency': "EUR",
    'category': 'Sales',
}
