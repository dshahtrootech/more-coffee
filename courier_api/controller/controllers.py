# -*- coding: utf-8 -*-
import base64
import json
import logging
from datetime import datetime
from odoo import _
# from .utils import *
from odoo.http import request

import pytz
from odoo.tools.misc import DEFAULT_SERVER_DATETIME_FORMAT

from odoo import http, fields

_logger = logging.getLogger(__name__)


class CourierCourier(http.Controller):
    @http.route(['/api/booking_form'],method="POST", auth='user', type='json')
    def booking_form(self, **kw):
        print(" * * *  *rr  * ** ** *  * *")
        vals = []

        courier = request.env['courier.courier']
        if kw:
            if kw.get("sender"):
                sender_details = kw.get("sender")
                sender = request.env["res.partner"].search([
                    ("name", "=", sender_details.get("sender_name")),
                    ("email", "=", sender_details.get("email")),
                    ("mobile", "=", sender_details.get("mobile"))], limit=1)
                if sender_details.get("sender_city"):
                    city = request.env['city.city'].search([
                        ('name', '=', sender_details.get('sender_city'))], limit=1)
                if sender_details.get("sender_area"):
                    area = request.env['area.area'].search([
                        ('name', '=', sender_details.get('sender_area'))], limit=1)

                if not sender:
                    if not city:
                        city = request.env['city.city'].create({
                            'name': sender_details.get('sender_city'),
                        })
                    if not area:
                        area = request.env['area.area'].create({
                            'name': sender_details.get('sender_area'),
                            'city_id': city.id or False
                        })

                    new_sender = {
                        "name": sender_details.get("sender_name"),
                        "email" : sender_details.get("email"),
                        "mobile" : sender_details.get("mobile"),
                        "city_id": city.id or '',
                        "area_id": area.id or '',
                    }
                    sender = request.env["res.partner"].create(new_sender)

            if kw.get("receiver"):
                receiver_details = kw.get("receiver")
                receiver = request.env["res.partner"].search([
                    ("name", "=", receiver_details.get("receiver_name")),
                    ("email", "=", receiver_details.get("email")),
                    ("mobile", "=", receiver_details.get("mobile"))],limit=1)

                if receiver_details.get("receiver_city"):
                    city = request.env['city.city'].search([
                        ('name', '=', receiver_details.get('receiver_city'))], limit=1)
                if receiver_details.get("receiver_area"):
                    area = request.env['area.area'].search([
                        ('name', '=', receiver_details.get('receiver_area'))], limit=1)

                if not receiver:
                    if not city:
                        city = request.env['city.city'].create({
                            'name': receiver_details.get('receiver_city'),
                        })
                    if not area:
                        area = request.env['area.area'].create({
                            'name': receiver_details.get('receiver_area'),
                            'city_id': city.id or False
                        })
                    new_receiver = {
                        "name": receiver_details.get("receiver_name"),
                        "email" : receiver_details.get("email"),
                        "mobile" : sender_details.get("mobile"),
                        "city_id": city.id or '',
                        "area_id": area.id or '',
                    }
                    print(new_receiver)
                    receiver = request.env["res.partner"].create(new_receiver)

            if kw.get("delivery_type"):
                if kw.get("delivery_type") == "Export":
                    delivery_type = 'normal_delivery'
                if kw.get("delivery_type") == "Import":
                    delivery_type = 'same_day_delivery'
                if kw.get("delivery_type") == "Domestic":
                    delivery_type = 'express_delivery'

            if kw.get("packages"):
                fbno_tree_id = []
                for rec in kw.get('packages'):
                    z = (0, 0, {
                        'product_description': rec['product_description'],
                        'length': rec['length'],
                        'height': rec['height'],
                        'width': rec['width'],
                        'weight': rec['weight']
                    })
                    fbno_tree_id.append(z)

            if kw.get('courier_type'):
                courier_type = request.env['courier.type'].search([
                    ('name', '=', kw.get('courier_type'))], limit=1)
                if not courier_type:
                    courier_type = request.env['courier.type'].create({
                        'name': kw.get('courier_type'),
                    })

            cod = False
            cod_amount = 0
            if kw.get('cod') == "True":
                if kw.get('cod_amount'):
                    cod = True
                    cod_amount = kw.get('cod_amount')


            vals = {
                "sender_id": sender.id,
                "receiver_id": receiver.id,
                'delivery_type': delivery_type,
                'fbno_tree_id': fbno_tree_id,
                'courier_type_id': courier_type.id,
                'cod' : cod,
                'cod_amount' : cod_amount,
            }
            # print(vals)

        try:
            courier = request.env['courier.courier'].create(vals)
            return {"msg": "success", "record_id": courier.id}
        except Exception as e:
            return {"msg": e, "record_id": False}

    @http.route(['/api/track_courier'], method="GET", auth='user', type='json')
    def track_courier(self, **kw):
        print("ok")
        if kw:
            courier = request.env['courier.courier'].sudo().search([
                ('courier_number', '=', kw.get("courier_number"))])
            if courier:

                if courier.delivery_type == 'express_delivery':
                    if courier.state_express == 'invoiced':
                        state = 'invoiced'
                        mail_tracking_value = request.env['mail.tracking.value'].sudo().search([
                            ('mail_message_id.record_name', '=', courier.courier_number),
                            ('new_value_char', 'in', ['Invoiced'])
                        ], order='write_date asc')
                        state_date = [datetime.strftime(
                            pytz.utc.localize(
                                datetime.strptime(
                                    str(mtv.write_date).split('.')[0],
                                    DEFAULT_SERVER_DATETIME_FORMAT)
                            ).astimezone(pytz.timezone(request.env.user.tz or pytz.utc)), "%c") for mtv in
                            mail_tracking_value]
                    if courier.state_express == 'assigned':
                        state = 'invoiced', 'assigned'
                        mail_tracking_value = request.env['mail.tracking.value'].sudo().search([
                            ('mail_message_id.record_name', '=', courier.courier_number),
                            ('new_value_char', 'in', ['Invoiced', 'Assigned To Driver'])
                        ], order='write_date asc')
                        state_date = [datetime.strftime(
                            pytz.utc.localize(
                                datetime.strptime(
                                    str(mtv.write_date).split('.')[0],
                                    DEFAULT_SERVER_DATETIME_FORMAT)
                            ).astimezone(pytz.timezone(request.env.user.tz or pytz.utc)), "%c") for mtv in
                            mail_tracking_value]
                    if courier.state_express == 'picked' \
                            or \
                            courier.state_express == 'assigned_to_driver':
                        state = 'invoiced', 'assigned', 'Picked'
                        mail_tracking_value = request.env['mail.tracking.value'].sudo().search([
                            ('mail_message_id.record_name', '=', courier.courier_number),
                            ('new_value_char', 'in', ['Invoiced', 'Assigned To Driver', 'Picked'])
                        ], order='write_date asc')
                        state_date = [datetime.strftime(
                            pytz.utc.localize(
                                datetime.strptime(
                                    str(mtv.write_date).split('.')[0],
                                    DEFAULT_SERVER_DATETIME_FORMAT)
                            ).astimezone(pytz.timezone(request.env.user.tz or pytz.utc)), "%c") for mtv in
                            mail_tracking_value]
                    if courier.state_express == 'delivered':
                        state = 'invoiced', 'assigned', 'Picked', 'delivered'
                        mail_tracking_value = request.env['mail.tracking.value'].sudo().search([
                            ('mail_message_id.record_name', '=', courier.courier_number),
                            ('new_value_char', 'in', ['Invoiced', 'Assigned To Driver', 'Picked', 'Delivered'])
                        ], order='write_date asc')
                        state_date = [datetime.strftime(
                            pytz.utc.localize(
                                datetime.strptime(
                                    str(mtv.write_date).split('.')[0],
                                    DEFAULT_SERVER_DATETIME_FORMAT)
                            ).astimezone(pytz.timezone(request.env.user.tz or pytz.utc)), "%c") for mtv in
                            mail_tracking_value]

                if courier.delivery_type != 'express_delivery':
                    if courier.state == 'invoiced':
                        state = 'invoiced'
                        mail_tracking_value = request.env['mail.tracking.value'].sudo().search([
                            ('mail_message_id.record_name', '=', courier.courier_number),
                            ('new_value_char', 'in', ['Invoiced'])
                        ], order='write_date asc')
                        state_date = [datetime.strftime(
                            pytz.utc.localize(
                                datetime.strptime(
                                    str(mtv.write_date).split('.')[0],
                                    DEFAULT_SERVER_DATETIME_FORMAT)
                            ).astimezone(pytz.timezone(request.env.user.tz or pytz.utc)), "%c") for mtv in
                            mail_tracking_value]
                    if courier.state == 'assigned':
                        state = 'invoiced', 'assigned'
                        mail_tracking_value = request.env['mail.tracking.value'].sudo().search([
                            ('mail_message_id.record_name', '=', courier.courier_number),
                            ('new_value_char', 'in', ['Invoiced', 'Assigned To Driver'])
                        ], order='write_date asc')
                        state_date = [datetime.strftime(
                            pytz.utc.localize(
                                datetime.strptime(
                                    str(mtv.write_date).split('.')[0],
                                    DEFAULT_SERVER_DATETIME_FORMAT)
                            ).astimezone(pytz.timezone(request.env.user.tz or pytz.utc)), "%c") for mtv in
                            mail_tracking_value]
                    if courier.state == 'Picked':
                        state = 'invoiced', 'assigned', 'Picked'
                        mail_tracking_value = request.env['mail.tracking.value'].sudo().search([
                            ('mail_message_id.record_name', '=', courier.courier_number),
                            ('new_value_char', 'in', ['Invoiced', 'Assigned To Driver', 'Picked'])
                        ], order='write_date asc')
                        state_date = [datetime.strftime(
                            pytz.utc.localize(
                                datetime.strptime(
                                    str(mtv.write_date).split('.')[0],
                                    DEFAULT_SERVER_DATETIME_FORMAT)
                            ).astimezone(pytz.timezone(request.env.user.tz or pytz.utc)), "%c") for mtv in
                            mail_tracking_value]
                    if courier.state == 'inscan':
                        state = 'invoiced', 'assigned', 'Picked', 'inscan'
                        mail_tracking_value = request.env['mail.tracking.value'].sudo().search([
                            ('mail_message_id.record_name', '=', courier.courier_number),
                            ('new_value_char', 'in', ['Invoiced', 'Assigned To Driver', 'Picked', 'Inscan'])
                        ], order='write_date asc')
                        state_date = [datetime.strftime(
                            pytz.utc.localize(
                                datetime.strptime(
                                    str(mtv.write_date).split('.')[0],
                                    DEFAULT_SERVER_DATETIME_FORMAT)
                            ).astimezone(pytz.timezone(request.env.user.tz or pytz.utc)), "%c") for mtv in
                            mail_tracking_value]
                    if courier.state == 'outscan':
                        state = 'invoiced', 'assigned', 'Picked', 'inscan'
                        mail_tracking_value = request.env['mail.tracking.value'].sudo().search([
                            ('mail_message_id.record_name', '=', courier.courier_number),
                            ('new_value_char', 'in', ['Invoiced', 'Assigned To Driver', 'Picked', 'Inscan'])
                        ], order='write_date asc')
                        state_date = [datetime.strftime(
                            pytz.utc.localize(
                                datetime.strptime(
                                    str(mtv.write_date).split('.')[0],
                                    DEFAULT_SERVER_DATETIME_FORMAT)
                            ).astimezone(pytz.timezone(request.env.user.tz or pytz.utc)), "%c") for mtv in
                            mail_tracking_value]
                    if courier.state == 'assigned_to_driver':
                        state = 'invoiced', 'assigned', 'Picked', \
                                'inscan', 'assigned_to_driver'
                        mail_tracking_value = request.env['mail.tracking.value'].sudo().search([
                            ('mail_message_id.record_name', '=', courier.courier_number),
                            ('new_value_char', 'in', ['Invoiced', 'Assigned To Driver',
                                                      'Picked', 'Inscan', 'Assigned driver For delivery'])
                        ], order='write_date asc')
                        state_date = [datetime.strftime(
                            pytz.utc.localize(
                                datetime.strptime(
                                    str(mtv.write_date).split('.')[0],
                                    DEFAULT_SERVER_DATETIME_FORMAT)
                            ).astimezone(pytz.timezone(request.env.user.tz or pytz.utc)), "%c") for mtv in
                            mail_tracking_value]
                    if courier.state == 'out_for_delivery':
                        state = 'invoiced', 'assigned', 'Picked', \
                                'inscan', 'assigned_to_driver'
                        mail_tracking_value = request.env['mail.tracking.value'].sudo().search([
                            ('mail_message_id.record_name', '=', courier.courier_number),
                            ('new_value_char', 'in', ['Invoiced', 'Assigned To Driver', 'Picked', 'Inscan',
                                                      'Assigned driver For delivery'])
                        ], order='write_date asc')
                        state_date = [datetime.strftime(
                            pytz.utc.localize(
                                datetime.strptime(
                                    str(mtv.write_date).split('.')[0],
                                    DEFAULT_SERVER_DATETIME_FORMAT)
                            ).astimezone(pytz.timezone(request.env.user.tz or pytz.utc)), "%c") for mtv in
                            mail_tracking_value]
                    if courier.state == 'delivered':
                        state = 'invoiced', 'assigned', 'Picked', \
                                'inscan', 'outscan', 'assigned_to_driver', \
                                'out_for_delivery', 'delivered'
                        mail_tracking_value = request.env['mail.tracking.value'].sudo().search([
                            ('mail_message_id.record_name', '=', courier.courier_number),
                            ('new_value_char', 'in', ['Invoiced', 'Assigned To Driver', 'Picked', 'Inscan',
                                                      'Assigned driver For delivery', 'Out for Delivery', 'Delivered'])
                        ], order='write_date asc')
                        state_date = [datetime.strftime(
                            pytz.utc.localize(
                                datetime.strptime(
                                    str(mtv.write_date).split('.')[0],
                                    DEFAULT_SERVER_DATETIME_FORMAT)
                            ).astimezone(pytz.timezone(request.env.user.tz or pytz.utc)), "%c") for mtv in
                            mail_tracking_value]

                return {
                    'success': True,
                    'error': None,
                    'message': 'Success',
                    'courier' : courier,
                    'sate' : state,
                    'state_date' : state_date
                }
            else:
                return {
                    'success': True,
                    'error': None,
                    'message': 'No courier found!'
                }

    @http.route(['/api/list/ongoing_delivery'], method="GET", auth='user', type='json')
    def ongoing_delivery(self, **kw):
        print("ok")
        couriers = request.env['courier.courier'].sudo().search(['|',
                            ('state', 'in', ['outscan','assigned_to_driver','out_for_delivery']),
                            ('state_express','in',['assigned_to_driver'])])
        lines = []
        for rec in couriers:
            cod_amount = 0
            cod = 'No'
            if rec.cod == True:
                cod='Yes'
                cod_amount = rec.cod_amount
            vals = {
                'courier_number' : rec.courier_number,
                'booking_date' : rec.today,
                'sender_name' : rec.sender_id.name,
                'receiver_name': rec.receiver_id.name,
                'courier_type' : rec.courier_type_id.name,
                'cod': cod,
                'cod_amount' : cod_amount,

            }
            lines.append(vals)

        return {
            'success': True,
            'error': None,
            'record': lines
        }


    @http.route('/api/get_contacts_data/', auth='user', type='json')
    def courier_contacts_data(self, **kw):
        """ Method to read the API """
        values = {}
        res_partner = request.env['res.partner']
        contact_ids = []
        for i in res_partner.sudo().search([]):
            contact_ids.append({"id": i.id,
                                "name": i.name,
                                "city_id": {"id": i.city_id.id if i.city_id else "",
                                            "name": i.city_id.name if i.city_id else ""},
                                'mobile': i.mobile,
                                "street": i.street,
                                "street2": i.street2,
                                "area_id": {"id": i.area_id.id if i.area_id else "",
                                            "name": i.area_id.name if i.area_id else ""},

                                })
        values['contact_datas'] = contact_ids

        return values

    @http.route('/api/get_default_data/', auth='user', type='json')
    def courier_default_value(self, **kw):
        """ Method to read the API """
        values = {}
        pickup_delivery_type = []
        delivery_type = []
        product_id = []
        pickup_delivery_type.append({"type": "export"})
        pickup_delivery_type.append({"type": "pickup_and_delivery"})
        pickup_delivery_type.append({"type": "delivery"})
        pickup_delivery_type.append({"type": "rto"})
        pickup_delivery_type.append({"type": "rts"})
        pickup_delivery_type.append({"type": "eid"})
        pickup_delivery_type.append({"type": "signature"})
        values["pickup_delivery_type"] = pickup_delivery_type


        product_id.append({"type": "small"})
        product_id.append({"type": "big"})
        product_id.append({"type": "box"})
        product_id.append({"type": "envelope"})
        product_id.append({"type": "plastic_bag"})
        product_id.append({"type": "cus_packing"})
        values["product_id"] = product_id

        delivery_type.append({"type": "express_delivery"})
        delivery_type.append({"type": "same_day_delivery"})
        delivery_type.append({"type": "normal_delivery"})
        values["delivery_type"] = delivery_type
        city_names = request.env['city.city']
        area_names = request.env['area.area']

        city_name = []
        for i in city_names.sudo().search([]):
            city_name.append({"id": i.id,
                               "name": i.name,

                                   })
        values['city_datas'] = city_name

        area_name = []
        for i in area_names.sudo().search([]):
            area_name.append({"id": i.id,
                              "name": i.name,

                              })
        values['area_datas'] = area_name

        return values

    @http.route('/api/manual_shipment_api', type='json', method="POST",
                auth="user")
    def create_manual_shipment(self, **kw):
        """ Create Shipment API"""
        vals = {}
        if kw:
            if 'senderName' in kw:
                sender_id = request.env['res.partner'].search([
                    ('name', '=', kw.get('senderName'))], limit=1)
                area_id = request.env['area.area'].search([
                    ('name', '=', kw.get('senderArea'))], limit=1)
                city_id = request.env['city.city'].search([
                    ('name', '=', kw.get('senderCity'))], limit=1)
                if 'senderArea' in kw:
                    if not city_id:
                        city_id = request.env['city.city'].create({
                            'name': kw.get('senderCity'),
                        })
                    if not area_id:
                        area_id = request.env['area.area'].create({
                            'name': kw.get('senderArea'),
                            'city_id': city_id and city_id.id or False
                        })
                if not sender_id:
                    sender_vals = {
                        'name': kw.get('senderName'),
                        'street': kw.get('senderstreet'),
                        'street2': kw.get('senderstreet2'),
                        'mobile': kw.get('senderMobileNumber'),
                        'email': kw.get('senderEmail'),
                        'city_id': city_id.id or '',
                        'area_id': area_id and area_id.id or False,

                    }
                    sender_id = request.env['res.partner'].create(sender_vals)
                vals['sender_id'] = sender_id and sender_id.id
            if 'receiverName' in kw:
                receiver_id = request.env['res.partner'].search([
                    ('name', '=', kw.get('receiverName'))], limit=1)
                area_id = request.env['area.area'].search([
                    ('name', '=', kw.get('receiverArea'))], limit=1)
                city_id = request.env['city.city'].search([
                    ('name', '=', kw.get('receiverCity'))], limit=1)
                if 'receiverArea' in kw:
                    if not city_id:
                        city_id = request.env['city.city'].create({
                            'name': kw.get('receiverCity'),
                        })
                    if not area_id:
                        area_id = request.env['area.area'].create({
                            'name': kw.get('receiverArea'),
                            'city_id': city_id and city_id.id or False
                        })
                if not receiver_id:
                    receiver_vals = {
                        'name': kw.get('receiverName'),
                        'street': kw.get('receiverstreet'),
                        'street2': kw.get('receiverstreet2'),
                        'mobile': kw.get('receiverMobileNumber'),
                        'email': kw.get('receiverEmail'),
                        'city_id': city_id.id or '',
                        'area_id': area_id and area_id.id or False,

                    }
                    receiver_id = request.env['res.partner'].create(receiver_vals)
                vals['receiver_id'] = receiver_id and receiver_id.id


            if 'Specialinstrction' in kw:
                    vals.update({
                        'spcl_del_instrn': kw.get('Specialinstrction')
                    })

            if 'declaredValue' in kw:
                    vals.update({
                        'declared_value': kw.get('declaredValue')
                    })

            if 'cod' in kw:
                if kw.get('cod') == 1:
                    vals.update({
                        'cod': True,
                        'cod_amount': kw.get('codAmount')
                    })

            if 'package' in kw:
                fbno_tree_id = []
                for i in kw.get('package'):
                    z = (0, 0, {
                        'product_description': i['description'],
                        'product_packaging_id': i['product_id'],
                        'length': i['length'],
                        'height': i['height'],
                        'width': i['width'],
                        'weight': i['weight']
                    })
                    fbno_tree_id.append(z)
                vals.update({
                    'fbno_tree_id': fbno_tree_id})

            if 'packageType' in kw:
                if kw.get('packageType') == 'pickup_and_delivery':
                    vals.update({
                        'pickup_delivery_type': kw.get('packageType')
                    })
                if kw.get('packageType') == 'delivery':
                    vals.update({
                        'pickup_delivery_type': kw.get('packageType')
                    })
                if kw.get('packageType') == 'rts':
                    vals.update({
                        'pickup_delivery_type': kw.get('packageType')
                    })

            if 'serviceType' in kw:
                if kw.get('serviceType') == 'express_delivery':
                    vals.update({
                        'delivery_type': kw.get('serviceType')
                    })
                if kw.get('serviceType') == 'same_day_delivery':
                    vals.update({
                        'delivery_type': kw.get('serviceType')
                    })
                if kw.get('serviceType') == 'normal_delivery':
                    vals.update({
                        'delivery_type': kw.get('serviceType')
                    })

            if 'courierNumber' in kw:
                man_number = kw.get('courierNumber')
                courier_num = request.env["courier.courier"].search([])
                num_map = courier_num.mapped('courier_number')
                if man_number in num_map:
                    print("DANGER")
                    return {
                        'msg': _("%s This Airway bill number is already existed!") % (man_number),
                    }
                else:
                    vals.update({
                        'courier_number': kw.get('courierNumber')
                    })
            if 'sender_id' and 'receiver_id' and 'pickup_delivery_type' and 'delivery_type' in vals:
                courier_id = request.env['courier.courier'].create(vals)
                courier_id.write({'assign_driver': request.env.user})
                if kw.get('serviceType') == 'express_delivery':
                    courier_id.action_pickedex()
                if kw.get('serviceType') != 'express_delivery':
                    courier_id.action_Picked()
                return {
                    'title': _('Shipment Created'),
                    'msg': _("%s Shipment is Created!") % (courier_id.courier_number),
                    'courier_id': courier_id and courier_id.id,
                    'delivery_charges': courier_id.fbno_delivery_total,
                    'cod': courier_id.cod_amount
                }

    @http.route('/api/get_shipment_count/', auth='user', type='json')
    def get_shipment_count(self, **kw):
        print('courier_count', kw)
        if kw:
            courier = request.env["courier.courier"].search_count([("sender_id", "=", kw.get("sender_id"))])
            print(courier)
            courier_count = {
                "count": courier,
            }
            return courier_count

    @http.route('/api/get_user_details/', auth='user', type='json')
    def get_user_details(self, **kw):
        print('heo', kw)
        if kw:
            user = request.env["res.partner"].search([("id", "=", kw.get("id"))], limit=1)
            print(user)
            user_details = {
                "name": user.name,
                "email": user.email,
                "id": user.id

            }
            return user_details

    @http.route('/api/edit_profile/', auth='user', type='json')
    def edit_profile(self, **kw):
        print('edit_profile', kw)
        if kw:
            user = request.env["res.partner"].search([("id", "=", kw.get("id"))], limit=1)
            print(len(user))
            if len(user) == 1:
                vals = {
                    "name": kw.get("name")
                }
                edit_user = user.write(vals)
                print(edit_user)
                if edit_user:
                    return {"msg": "success"}
            else:
                return {"msg": "No user found"}
