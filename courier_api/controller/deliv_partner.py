# -*- coding: utf-8 -*-
import base64
import datetime
import json
import pytz

from odoo import fields, http, _
from odoo.http import request
from dateutil.relativedelta import relativedelta



class DelivLoginAPI(http.Controller):

    @http.route(
        ['/api/checkin_status/<int:user_id>'],
        auth='user', type='json', method="POST")
    def checkin_status(self, user_id, **kw):
        """ checkin_status"""
        user_id = request.env["res.users"].search([
            ("id", "=", int(user_id))], limit=1)
        att_id = request.env["hr.attendance"].search([
            ("employee_id", "=", request.env.user.employee_id.id)], limit=1)
        user_tz = pytz.timezone(request.env.context.get('tz') or request.env.user.tz)
        if kw and 'check_in' in kw:
            dd = datetime.datetime.strptime(kw.get('check_in'), "%Y-%m-%d %H:%M:%S")
            local_datetime = user_tz.localize(dd, is_dst=None)
            aa = local_datetime.astimezone(pytz.utc)
            i = datetime.datetime.strftime(aa, "%Y-%m-%d %H:%M:%S")
            vals = {'check_in': i}
            attendance_id = request.env['hr.attendance'].create(vals)
            return {
                'msg': _("Check in success !"),
            }

    @http.route(
        ['/api/checkout_status/<int:user_id>'],
        auth='user', type='json', method="POST")
    def checkout_status(self, user_id, **kw):
        """ checkout_status"""
        user_id = request.env["res.users"].search([
            ("id", "=", int(user_id))], limit=1)
        atts_id = request.env["hr.attendance"].search([
            ("employee_id", '=', request.env.user.employee_id.id),('check_out', '=', False)], limit=1)
        user_tz = pytz.timezone(request.env.context.get('tz') or request.env.user.tz)
        if kw and 'check_out' in kw:
            dd = datetime.datetime.strptime(kw.get('check_out'), "%Y-%m-%d %H:%M:%S")
            local_datetime = user_tz.localize(dd, is_dst=None)
            aa = local_datetime.astimezone(pytz.utc)
            i = datetime.datetime.strftime(aa, "%Y-%m-%d %H:%M:%S")
            vals = {'check_out': i}
            attendance_id = atts_id.write(vals)
            return {
                'msg': _("Check Out success !"),
            }

    @http.route(
        ['/api/online_offline_status/<int:user_id>'],
        auth='user', type='json', method="POST")
    def online_offline_status(self, user_id, **kw):
        """ online_offline_status"""
        if kw and 'is_online' in kw:
            user_id = request.env["res.users"].search([
                ("id", "=", int(user_id))], limit=1)
            user_id.is_on_off_status = True\
                if kw.get('is_online') == 'True' else False
            return {
                'title': _('Toggle Online/Offline'),
                'msg': _("Online Offline Status!"),
                'status': 'On' if kw.get('is_online') == 'True' else 'Off'
            }

    @http.route(
        ['/api/get/my_route_shipmemt/<int:courier_id>'],
        auth='user', type='json', method="POST")
    def my_route_shipmemt(self, courier_id, **kw):
        """ Get the My Route Driver current location and receiver location"""
        if courier_id:
            receiver_id = request.env["courier.courier"].search([
                ("id", "=", int(courier_id))], limit=1).receiver_id
            if receiver_id and not\
                (receiver_id.partner_latitude or
                    receiver_id.partner_longitude):
                receiver_id.geo_localize()
            my_route_shipmemt = {
                "receiver_latitude": receiver_id.partner_latitude,
                "receiver_longitude": receiver_id.partner_longitude
            }
            return my_route_shipmemt

    @http.route(
        ['/api/get/delivery_shipmemt/<int:courier_id>'],
        auth='user', type='json', method="POST")
    def get_delivery_shipmemt(self, courier_id, **kw):
        """ Get the Shipmemt Specific Infrormation"""
        if courier_id:
            courier_id = request.env["courier.courier"].search([
                ("id", "=", int(courier_id)),
                ('pickup_delivery_type', '=', 'delivery')], limit=1)
            courier_state = courier_id.state_express if courier_id.delivery_type == 'express_delivery' else courier_id.state
            courier_details = {
                "status": courier_state,
                "delivery_type": courier_id.delivery_type
            }
            return courier_details

    @http.route(
        ['/api/get/collection_shipmemt/<int:courier_id>'],
        auth='user', type='json', method="POST")
    def get_collection_shipmemt(self, courier_id, **kw):
        """ Get the Collection Shipmemt Specific Infrormation"""
        if courier_id:
            courier_id = request.env["courier.courier"].search([
                ("id", "=", int(courier_id)),
                ('pickup_delivery_type', '=', 'pickup_and_delivery')], limit=1)
            courier_state = courier_id.state_express if courier_id.delivery_type == 'express_delivery' else courier_id.state
            collection_ship_detail = {
                "status": courier_state,
                "delivery_type": courier_id.delivery_type,
                "Area": courier_id.receiver_id.area_id.name,
                "area_id": courier_id.receiver_id.area_id and courier_id.receiver_id.area_id.id or False,
            }
            return collection_ship_detail

    @http.route(
        ['/api/get/delivery_status/<int:courier_id>'],
        auth='user', type='json', method="POST")
    def get_non_delivery_status(self, courier_id, **kw):
        """ Get the hipmemt Specific Infrormation Status"""
        if courier_id:
            courier_id = request.env["courier.courier"].search([
                ("id", "=", int(courier_id))], limit=1)
            courier_state = courier_id.state_express if courier_id.delivery_type == 'express_delivery' else courier_id.state
            ship_detail = {
                "status": courier_state
            }
            return ship_detail

    @http.route(
        ['/api/proof_of_delivery/<int:courier_id>'],
        type='http', method="POST", auth="user", csrf=False)
    def proof_of_delivery(self, courier_id, **kw):
        """ Proof Of Delivery"""
        if courier_id and 'filename' in kw:
            courier_id = request.env["courier.courier"].search([
                ("id", "=", int(courier_id))], limit=1)
            try:
                for k, v in kw.items():
                    courier_id.write({
                        'packg_img': base64.encodebytes(v.stream.read())})
                return json.dumps(
                    {
                        'status': 'success', 'courier_id': courier_id.id})
            except:
                return json.dumps(
                    {
                        'status': 'error', 'status_code': 500})

    @http.route('/api/cancel_shipment_api', type='json', method="POST",
                auth="user")
    def cancel_shipment(self, **kw):
        """ Cancel Shipment """
        if kw and 'shipment_id' in kw:
            courier_id = request.env['courier.courier'].search([
                ('id', '=', int(kw.get('shipment_id')))], limit=1)
            courier_number = courier_id.courier_number
            courier_id.cancel_courier_express()
            return {
                'title': _('Shipment Cancel'),
                'msg': _("%s Shipment is Cancel!") % (courier_number),
                'status': 'Cancel'
            }

    @http.route([
        '/api/shipment_cancel_list'],
        auth='user', type='json', method="POST")
    def shipment_cancel_list(self, **kw):
        """ shipment_cancel_list """
        courier_ids = request.env['courier.courier'].search([
            ('state', '=', 'cancel')]).ids
        return courier_ids or False

    @http.route(['/api/collect_cash_payment/<int:courier_id>'],
                type='json', method="POST",
                auth="user")
    def collect_cash_payment(self, courier_id, **kw):
        """ collect_cash_payment """
        if courier_id:
            courier_id = request.env['courier.courier'].search([
                ('id', '=', int(courier_id))], limit=1)
            courier_id.write({
                'cod': True if kw.get('is_cod') == 'True' else False,
                'cod_amount': kw.get('cod_amount')})
            return {
                'title': _('Collect Cash Payment Updated'),
                'msg': _("Collect Cash Payment Updated!"),
                'status': 'Updated'
            }

    @http.route(['/api/shipment_cancel_reason/<int:courier_id>'],
                type='json', method="POST",
                auth="user")
    def shipment_cancel_reason(self, courier_id, **kw):
        """ Shipment Cancel Reason List API """
        if courier_id:
            courier_id = request.env['courier.courier'].search([
                ('id', '=', int(courier_id))], limit=1)
            courier_id.fbno_invoice_id.button_cancel()
            courier_id.write({
                'state_express': 'cancel',
                'status': 'Cancel',
                'fbno_cancel_reason': kw.get('cancel_reason')})
            return {
                'title': _('Shipment Cancel Reason'),
                'msg': _("Shipment Cancel Reason!"),
                'status': 'Cancelled'
            }

    @http.route(['/api/shipment_not_delivery_reason/<int:courier_id>'],
                type='json', method="POST",
                auth="user")
    def shipment_not_delivery_reason(self, courier_id, **kw):
        """ Shipment not delivery reason list API """
        if courier_id:
            courier_id = request.env['courier.courier'].search([
                ('id', '=', int(courier_id))], limit=1)
            courier_id.write(
                {
                 'fbno_shipment_not_delivery': kw.get('shipment_not_delivered')
                })
            return {
                'title': _('Shipment not Delivery Reason'),
                'msg': _("Shipment not Delivery Reason!"),
                'status': 'Not Delivered'
            }

    @http.route([
                '/api/contact_us_detail/<int:user_id>'],
                type='json', method="get",
                auth="user")
    def contact_us_detail(self, user_id, **kw):
        """ Contact us details API """
        if user_id:
            user_id = request.env['res.users'].search([
                ('id', '=', int(user_id))], limit=1)
            driver_user_details = {
                'contact_email': user_id.driver_manager_id.email,
                'contact_phone': user_id.driver_manager_id.phone or user_id.driver_manager_id.mobile,
            }
            return driver_user_details

    @http.route(['/api/current_month_payment_daywise'],
                type='json', method="get",
                auth="user")
    def current_month_payment_daywise(self, **kw):
        """ current_month_payment_daywise """
        moves = request.env['account.move'].search([])
        data = moves.current_month_payment()
        return data

    @http.route(['/api/prev_month_payment_daywise'],
                type='json', method="get",
                auth="user")
    def prev_month_payment_daywise(self, **kw):
        """ prev_month_payment_daywise """
        moves = request.env['account.move'].search([])
        data = moves.previous_month_payment()
        return data

    @http.route([
        '/api/runsheet_list/<int:user_id>'],
        type='json', method="get", auth="user")
    def runsheet_list(self, user_id, **kw):
        """ runsheet list API """
        if user_id:
            courier_ids = request.env['courier.courier'].search_count(
                [
                    ('assign_driver', '=', int(user_id))
                ]
            )
            return courier_ids

    @http.route([
        '/api/runsheet_detail/<int:user_id>'],
        type='json', method="get", auth="user")
    def runsheet_detail(self, user_id, **kw):
        """ runsheet details API """
        if user_id:
            courier_ids = request.env['courier.courier'].search(
                [
                    ('assign_driver', '=', int(user_id))
                ]
            )
            courier_list = [{
                    'courier_number': courier_id.courier_number,
                    'sender_id': courier_id.sender_id and courier_id.sender_id.id or False,
                    'receiver_id': courier_id.receiver_id and courier_id.receiver_id.id or False,
                    'pickup_time': courier_id.pickup_time,
                    'cod_amount': courier_id.cod_amount,
                    'receiver_id_phone': courier_id.receiver_id.phone,
                    'receiver_id_mobile': courier_id.receiver_id.mobile,
                } for courier_id in courier_ids]
            return courier_list

    @http.route([
        '/api/runsheet_scan_barcode/<int:user_id>'],
        type='json', method="POST", auth="user")
    def runsheet_scan_barcode(self, user_id, **kw):
        """ runsheet scan barcode API """
        if user_id:
            courier_id = request.env['courier.courier'].search(
                [
                    ('assign_driver', '=', int(user_id)),
                    ('courier_number', '=', kw.get('courier_number'))
                ], limit=1
            )
            courier_id.state_express = 'delivered'
            return {
                'title': _('Shipment Updated'),
                'msg': _("Runsheet Scan Courier - %s is Delivered!") % (courier_id.courier_number),
                'status': 'Delivered'
            }

    @http.route([
        '/api/task_log_counter/<int:user_id>'],
        type='json', method="get", auth="user")
    def task_log_counter(self, user_id, **kw):
        """ Task Log Counter API """
        if user_id:
            deliv_ship_cnt = request.env['courier.courier'].search_count(
                [
                    ('assign_driver', '=', int(user_id)),
                    ('pickup_delivery_type', '=', 'delivery'),
                    ('fbno_assign_driver_date', '=', fields.Date.today())
                ]
            )
            coll_ship_cnt = request.env['courier.courier'].search_count(
                [
                    ('assign_driver', '=', int(user_id)),
                    ('pickup_delivery_type', '=', 'pickup_and_delivery'),
                    ('fbno_assign_driver_date', '=', fields.Date.today())
                ]
            )
            return {
                'deliv_ship_cnt': deliv_ship_cnt,
                'coll_ship_cnt': coll_ship_cnt
            }

    @http.route([
        '/api/collect_collection/<int:user_id>/<int:courier_id>'],
        type='json', method="get", auth="user")
    def collect_collection(self, user_id, courier_id, **kw):
        """ collect_collection """
        if user_id:
            coll_ship_id = request.env['courier.courier'].search(
                [
                    ('assign_driver', '=', int(user_id)),
                    ('pickup_delivery_type', '=', 'pickup_and_delivery'),
                    ('id', '=', int(courier_id))
                ]
            )
            if kw.get('collect_status') and kw.get('collect_status') == 'collect':
                coll_ship_id.write({
                        'state': 'picked',
                        'state_express': 'picked',
                        'fbno_collect_to': kw.get('collect_to') if kw.get('collect_to') else False,
                        'pickup_time': datetime.datetime.strptime(str(kw.get('pickup_date')) + ' ' + str(kw.get('pickup_time')), "%Y-%m-%d %H:%M:%S"),
                        'fno_collect_comment': kw.get('collect_comment')
                    }
                )
                return {
                    'Title': _("Collect Collection"),
                    'msg': _("Collect Collection is Completed"),
                    'Collect Shipment': coll_ship_id and coll_ship_id.id or False,
                    'Status': 'Collected'
                }
            return {'Status': 'Not Collected'}

    @http.route([
        '/api/not_collect_collection/<int:user_id>/<int:courier_id>'],
        type='json', method="get", auth="user")
    def not_collect_collection(self, user_id, courier_id, **kw):
        """ not_collect_collection """
        if user_id:
            coll_ship_id = request.env['courier.courier'].search(
                [
                    ('assign_driver', '=', int(user_id)),
                    ('pickup_delivery_type', '=', 'pickup_and_delivery'),
                    ('id', '=', int(courier_id))
                ]
            )
            if kw.get('collect_status') and kw.get('collect_status') == 'not_collect':
                coll_ship_id.write({
                        'state': 'unpicked',
                        'state_express': 'unpicked',
                        'fbno_not_collect_reason': kw.get('not_collect_reason') if kw.get('not_collect_reason') else False,
                        'pickup_time': datetime.datetime.strptime(str(kw.get('pickup_date')) + ' ' + str(kw.get('pickup_time')), "%Y-%m-%d %H:%M:%S"),
                        'fno_collect_comment': kw.get('collect_comment')
                    }
                )
                return {
                    'Title': _("Collect Collection"),
                    'msg': _("Collect Collection is Receoved as Not Collected"),
                    'Collect Shipment': coll_ship_id and coll_ship_id.id or False,
                    'Status': 'Collected'
                }
            return {'Status': 'Not Collected'}

    @http.route([
        '/api/dashboard_count/<int:user_id>'],
        type='json', method="get", auth="user")
    def dashboard_count(self, user_id, **kw):
        """ dashboard_count """
        couriers = request.env['courier.courier'].search(
                [
                    ('assign_driver', '=', int(user_id)),
                    ('cod', '=', True),
                    ('status', '=', 'Delivered')
                ], order="sender_id").ids
        aml = request.env['account.move.line'].sudo().search([('fbno_courier_ids', '!=', False)]).mapped('fbno_courier_ids').mapped('id')
        substract_couriet_data = set(couriers) - set(aml)
        couriers_data = request.env['courier.courier'].browse(substract_couriet_data)
        if user_id:
            return {
                # 'completed_trips': request.env['courier.courier'].search_count([('assign_driver', '=', int(user_id)), ('state', '=', 'delivered')]),
                'total_trips': request.env['res.users'].search([('id', '=', int(user_id))], limit=1).fbno_total_trip_delivered + request.env['res.users'].search([('id', '=', int(user_id))], limit=1).fbno_total_trip_picked,
                'pending_trips': request.env['res.users'].search([('id', '=', int(user_id))], limit=1).fbno_total_trip_delivered_pending + request.env['res.users'].search([('id', '=', int(user_id))], limit=1).fbno_total_trip_picked_pending,
                # 'cancel_trips': request.env['courier.courier'].search_count([('assign_driver', '=', int(user_id)), ('state', '=',  'cancel')]),
                'cah_on_hand': sum(couriers_data.mapped('cod_amount')),
                # 'today_total_trips': request.env['courier.courier'].search_count([('assign_driver', '=', int(user_id)), ('fbno_assign_driver_date', '=', fields.Date.today())]),
                # 'today_completed_trips': request.env['courier.courier'].search_count([('assign_driver', '=', int(user_id)), ('state', 'in', ['delivered', 'inscan']), ('fbno_assign_driver_date', '=', fields.Date.today())]),
                # 'today_pending_trips': request.env['courier.courier'].search_count([('assign_driver', '=', int(user_id)), ('state', 'in', ['outscan', 'out_for_delivery']), ('fbno_assign_driver_date', '=', fields.Date.today())]),
                # 'today_cancel_trips': request.env['courier.courier'].search_count([('assign_driver', '=', int(user_id)), ('state', '=',  'cancel'), ('fbno_assign_driver_date', '=', fields.Date.today())]),
                # 'cost_of_day': sum(request.env['courier.courier'].search([('assign_driver', '=', int(user_id)), ('fbno_assign_driver_date', '=', fields.Date.today())]).mapped('fbno_delivery_total'))
            }

    @http.route([
        '/api/get/delivery_shipmemt/<int:user_id>'],
        auth='user', type='json', method="get")
    def get_delivery_shipmemt(self, user_id, **kw):
        if user_id:
            courier_ids = request.env["courier.courier"].search([
                ('pickup_delivery_type', 'in', ['delivery', 'pickup_and_delivery']),
                ('status', 'in', ['Assigned driver For delivery', 'Out for Delivery']),
                ('assign_driver', '=', int(user_id))])
            courier_details = [{
                'courier_id': courier_id and courier_id.id or False,
                'Courier Number': courier_id.courier_number,
                "Delivery Type": courier_id.delivery_type,
                'Sender Name': courier_id.sender_id.name,
                'Receiver Name': courier_id.receiver_id.name,
                'Receiver mobile': courier_id.receiver_id.mobile,
                'Receiver street': courier_id.receiver_id.street,
                'Receiver street 2': courier_id.receiver_id.street2,
                'Receiver City': courier_id.receiver_id.city_id.name,
                'Receiver Area': courier_id.receiver_id.area_id.name,
                'Booked Date': courier_id.today.date(),
                'COD amount': courier_id.cod_amount,
                'No of Piecs': courier_id.fbno_total_box_cnt,
                'Warehouse': courier_id.ware_house_id.name,
                "status": courier_id.state_express if courier_id.delivery_type == 'express_delivery' else courier_id.state,
                'packages': [{'name':courier_line.product_description, 'barcode': courier_line.fbno_air_number} for courier_line in courier_id.fbno_tree_id]
            } for courier_id in courier_ids]
            return courier_details

    @http.route(
        ['/api/get/collection_shipmemt/<int:user_id>'],
        auth='user', type='json', method="get")
    def get_collection_shipmemt(self, user_id, **kw):
        if user_id:
            courier_ids = request.env["courier.courier"].search([
                ('pickup_delivery_type', 'in', ['delivery', 'pickup_and_delivery']),
                ('status', '=', 'Assigned To Driver'),
                ('assign_driver', '=', int(user_id))])
            collection_ship_detail = [{
                'courier_id': courier_id and courier_id.id or False,
                'Courier Number': courier_id.courier_number,
                "Delivery Type": courier_id.delivery_type,
                'Receiver Name': courier_id.receiver_id.name,
                'Sender Name': courier_id.sender_id.name,
                'Sender mobile': courier_id.sender_id.mobile,
                'Sender street': courier_id.sender_id.street,
                'Sender street 2': courier_id.sender_id.street2,
                'Sender City': courier_id.sender_id.city_id.name,
                'Sender Area': courier_id.sender_id.area_id.name,
                'Booked Date': courier_id.today.date(),
                'Delivery Total': courier_id.fbno_delivery_total,
                'COD amount': courier_id.cod_amount,
                'No of Piecs': courier_id.fbno_total_box_cnt,
                'Total': courier_id.fbno_delivery_total_collected,
                'Warehouse': courier_id.ware_house_id.name,
                "status": courier_id.state_express if courier_id.delivery_type == 'express_delivery' else courier_id.state,
                'packages': [{'name':courier_line.product_description, 'barcode': courier_line.fbno_air_number} for courier_line in courier_id.fbno_tree_id]
            } for courier_id in courier_ids]
            return collection_ship_detail

    @http.route(
        ['/api/get/delivery_hisotry/<int:user_id>'],
        auth='user', type='json', method="get")
    def delivery_hisotry(self, user_id, **kw):
        if user_id:
            delivery_courier_ids = request.env["courier.courier"].search([
                ('pickup_delivery_type', 'in', ['delivery', 'pickup_and_delivery']),
                ('assign_driver', '=', int(user_id)),
                ('status', 'in', ['Assigned driver For delivery', 'Out for Delivery', 'Delivered'])
            ]),
            courier_details = [{
                'booking_number': courier_id.courier_number,
                "Delivery Type": courier_id.delivery_type,
                'customer_name': courier_id.sender_id.name,
                'reciever name': courier_id.receiver_id.name,
                'area': courier_id.receiver_id.area_id.name,
                'city': courier_id.receiver_id.city_id.name,
                'delivery_type': dict(courier_id._fields['delivery_type'].selection).get(courier_id.delivery_type),
                'service_type': dict(courier_id._fields['pickup_delivery_type'].selection).get(courier_id.pickup_delivery_type),
                'Assign Date': courier_id.fbno_assign_driver_date,
                'Delivery Total': courier_id.fbno_delivery_total,
                'cod_amount': courier_id.fbno_delivery_total_collected,
                'Warehouse': courier_id.ware_house_id.name,
                "status": courier_id.state_express if courier_id.delivery_type == 'express_delivery' else courier_id.state,
            } for courier_id in delivery_courier_ids]
            return courier_details

    @http.route(
        ['/api/get/pickup_and_delivery_hisotry/<int:user_id>'],
        auth='user', type='json', method="get")
    def pickup_and_delivery_hisotry(self, user_id, **kw):
        if user_id:
            pickup_and_delivery_courier_ids = \
                request.env["courier.courier"].search(
                    [
                        ('pickup_delivery_type', 'in', ['delivery', 'pickup_and_delivery']),
                        ('assign_driver', '=', int(user_id)),
                        ('status', 'in', ['Assigned To Driver', 'Picked'])
                    ])
            collection_ship_detail = [{
                'booking_number': courier_id.courier_number,
                "Delivery Type": courier_id.delivery_type,
                'customer_name': courier_id.sender_id.name,
                'area': courier_id.sender_id.area_id.name,
                'city': courier_id.sender_id.city_id.name,
                'delivery_type': dict(courier_id._fields['delivery_type'].selection).get(courier_id.delivery_type),
                'service_type': dict(courier_id._fields['pickup_delivery_type'].selection).get(courier_id.pickup_delivery_type),
                'reciever name': courier_id.receiver_id.name,
                'Assign Date': courier_id.fbno_assign_driver_date,
                'Delivery Total': courier_id.fbno_delivery_total,
                'cod_amount': courier_id.fbno_delivery_total_collected,
                'Warehouse': courier_id.ware_house_id.name,
                "status": courier_id.state_express if courier_id.delivery_type == 'express_delivery' else courier_id.state,
            } for courier_id in pickup_and_delivery_courier_ids]
            return collection_ship_detail

    @http.route([
        '/api/delivery_report/<int:user_id>'],
        type='json', method="get", auth="user")
    def delivery_report(self, user_id, **kw):
        if user_id:
            return {
                'completed_trips': request.env['res.users'].search([('id', '=', int(user_id))], limit=1).fbno_total_trip_delivered_completed,
                'total_trips': request.env['res.users'].search([('id', '=', int(user_id))], limit=1).fbno_total_trip_delivered,
                'pending_trips': request.env['res.users'].search([('id', '=', int(user_id))], limit=1).fbno_total_trip_delivered_pending,
                'cancel_trips': request.env['res.users'].search([('id', '=', int(user_id))], limit=1).fbno_total_trip_delivered_cancle,
                # 'today_total_trips': request.env['courier.courier'].search_count([('pickup_delivery_type', '=', 'delivery'), ('assign_driver', '=', int(user_id)), ('fbno_assign_driver_date', '=', fields.Date.today())]),
                # 'today_completed_trips': request.env['courier.courier'].search_count([('pickup_delivery_type', '=', 'delivery'), ('assign_driver', '=', int(user_id)), ('state', 'in', ['delivered', 'inscan']), ('fbno_assign_driver_date', '=', fields.Date.today())]),
                # 'today_pending_trips': request.env['courier.courier'].search_count([('pickup_delivery_type', '=', 'delivery'), ('assign_driver', '=', int(user_id)), ('state', 'in', ['outscan', 'out_for_delivery']), ('fbno_assign_driver_date', '=', fields.Date.today())]),
                # 'today_cancel_trips': request.env['courier.courier'].search_count([('pickup_delivery_type', '=', 'delivery'), ('assign_driver', '=', int(user_id)), ('state', '=',  'cancel'), ('fbno_assign_driver_date', '=', fields.Date.today())]),
                # 'cost_of_day': sum(request.env['courier.courier'].search([('pickup_delivery_type', '=', 'delivery'), ('assign_driver', '=', int(user_id)), ('fbno_assign_driver_date', '=', fields.Date.today())]).mapped('fbno_delivery_total'))
            }

    @http.route([
        '/api/pickup_report/<int:user_id>'],
        type='json', method="get", auth="user")
    def pickup_report(self, user_id, **kw):
        if user_id:
            return {
                'completed_trips': request.env['res.users'].search([('id', '=', int(user_id))], limit=1).fbno_total_trip_picked_completed,
                'total_trips': request.env['res.users'].search([('id', '=', int(user_id))], limit=1).fbno_total_trip_picked,
                'pending_trips': request.env['res.users'].search([('id', '=', int(user_id))], limit=1).fbno_total_trip_picked_pending,
                'cancel_trips': request.env['res.users'].search([('id', '=', int(user_id))], limit=1).fbno_total_trip_picked_cancle,
                # 'today_total_trips': request.env['courier.courier'].search_count([('pickup_delivery_type', '=', 'pickup_and_delivery'), ('assign_driver', '=', int(user_id)), ('fbno_assign_driver_date', '=', fields.Date.today())]),
                # 'today_completed_trips': request.env['courier.courier'].search_count([('pickup_delivery_type', '=', 'pickup_and_delivery'), ('assign_driver', '=', int(user_id)), ('state', 'in', ['delivered', 'inscan']), ('fbno_assign_driver_date', '=', fields.Date.today())]),
                # 'today_pending_trips': request.env['courier.courier'].search_count([('pickup_delivery_type', '=', 'pickup_and_delivery'), ('assign_driver', '=', int(user_id)), ('state', 'in', ['outscan', 'out_for_delivery']), ('fbno_assign_driver_date', '=', fields.Date.today())]),
                # 'today_cancel_trips': request.env['courier.courier'].search_count([('pickup_delivery_type', '=', 'pickup_and_delivery'), ('assign_driver', '=', int(user_id)), ('state', '=',  'cancel'), ('fbno_assign_driver_date', '=', fields.Date.today())]),
                # 'cost_of_day': sum(request.env['courier.courier'].search([('pickup_delivery_type', '=', 'pickup_and_delivery'), ('assign_driver', '=', int(user_id)), ('fbno_assign_driver_date', '=', fields.Date.today())]).mapped('fbno_delivery_total'))
            }

    @http.route('/api/get_pick_del_default_field_value',
        type='json', method="POST", auth="user")
    def pickup_delivery_default_field_key_value(self, **kw):
        return {
            'pickup_failed': [value for value in (dict(request.env["courier.courier"]._fields['fbno_pickup_failed'].selection)).values()],
            'delivery_failed': [value for value in (dict(request.env["courier.courier"]._fields['fbno_delivery_failed'].selection)).values()],
            'delivery_rejected': [value for value in (dict(request.env["courier.courier"]._fields['fbno_delivery_rejected'].selection)).values()],
        }

    @http.route(
        ['/api/delivery_update_data/<int:courier_id>'],
        type='http', method="POST", auth="user", csrf=False)
    def delivery_update_data(self, courier_id, **kw):
        """ Proof Of Delivery"""
        def get_key(my_dict, val):
            for key, value in my_dict.items():
                if val.strip() == value.strip():
                    return key
        if courier_id:
            courier_id = request.env["courier.courier"].search([
                ("id", "=", int(courier_id))], limit=1).sudo()
            try:
                if kw.get('delivery_future'):
                    courier_id.write(
                        {
                        'fbno_delivery_future': datetime.datetime.strftime(
                            pytz.timezone(request.env.context.get('tz') or request.env.user.tz).localize(
                            datetime.datetime.strptime(
                                kw.get('delivery_future'), "%Y-%m-%d %H:%M:%S"),
                                is_dst=None).astimezone(pytz.utc), "%Y-%m-%d %H:%M:%S"),
                        'fbno_delivery_post': kw.get('status_update')
                        }
                    )
                    return json.dumps({'status': 'success', 'courier_id': courier_id.id})
                if kw.get('delivery_failed'):
                    courier_id.write(
                        {
                            'fbno_delivery_failed': get_key(dict(courier_id._fields['fbno_delivery_failed'].selection), kw.get('delivery_failed')),
                            'fbno_delivery_post': kw.get('status_update')
                        }
                    )
                    return json.dumps({'status': 'success', 'courier_id': courier_id.id})
                if kw.get('delivery_rejected'):
                    courier_id.write(
                        {
                            'fbno_delivery_rejected': get_key(dict(courier_id._fields['fbno_delivery_rejected'].selection), kw.get('delivery_rejected')),
                            'fbno_delivery_post': kw.get('status_update')
                        }
                    )
                    return json.dumps({'status': 'success', 'courier_id': courier_id.id})
                for k, v in kw.items():
                    if not v:
                        continue
                    if k == 'packg_img_scan_file':
                        courier_id.write({
                            'packg_img': base64.encodebytes(v.stream.read())})
                    if k == 'packg_img_filename_signature':
                        courier_id.write(
                            {
                                'fbno_packg_img_sign': base64.encodebytes(
                                    v.stream.read())})
                if kw.get('remarks'):
                    courier_id.fbno_remarks = kw.get('remarks')
                if kw.get('status_update') == 'delivery_success':
                    if courier_id.delivery_type == "express_delivery":
                        courier_id.write(
                            {
                                'state_express': 'delivered',
                                'status': 'Delivered'
                            })
                        mail_activity = request.env['mail.activity'].sudo().search([('res_name', '=', courier_id.courier_number)])
                        mail_activity.sudo().action_done()
                    else:
                        courier_id.assign_driver.fbno_total_trip_delivered_completed += 1
                        courier_id.assign_driver.fbno_total_trip_delivered_pending -= 1
                        courier_id.write(
                            {
                                'state': 'delivered',
                                'status': 'Delivered'
                            })
                        mail_activity = request.env['mail.activity'].sudo().search([('res_name', '=', courier_id.courier_number)])
                        mail_activity.sudo().action_done()
                else:
                    courier_id.fbno_delivery_post = kw.get('status_update')
                return json.dumps(
                    {
                        'status': 'success', 'courier_id': courier_id.id})
            except:
                return json.dumps(
                    {
                        'status': 'error', 'status_code': 500
                    })

    @http.route(
        ['/api/pickup_update_data/<int:courier_id>'],
        type='json', method="POST", auth="user")
    def pickup_update_data(self, courier_id, **kw):
        """ Proof Of Delivery"""
        def get_key(my_dict, val):
            for key, value in my_dict.items():
                if val.strip() == value.strip():
                    return key
        if courier_id:
            courier_id = request.env["courier.courier"].search([
                ("id", "=", int(courier_id))], limit=1).sudo()
            try:
                if kw.get('pickup_future'):
                    courier_id.write(
                        {
                            'fbno_pickup_future': datetime.datetime.strftime(
                                pytz.timezone(request.env.context.get('tz') or request.env.user.tz).localize(
                                datetime.datetime.strptime(
                                    kw.get('pickup_future'), "%Y-%m-%d %H:%M:%S"),
                                    is_dst=None).astimezone(pytz.utc), "%Y-%m-%d %H:%M:%S"),
                            'fbno_pickup_post': kw.get('status_update')
                        }
                    )
                    return {'status': 'success', 'courier_id': courier_id.id}
                if kw.get('pickup_failed'):
                    courier_id.write(
                        {
                            'fbno_pickup_failed': get_key(dict(courier_id._fields['fbno_pickup_failed'].selection), kw.get('pickup_failed')),
                            'fbno_pickup_post': kw.get('status_update')
                        }
                    )
                    return {'status': 'success', 'courier_id': courier_id.id}
                if courier_id.delivery_type == "express_delivery":
                    courier_id.write({'state_express': 'picked', 'status': 'Picked'})
                    mail_activity = request.env['mail.activity'].sudo().search([('res_name', '=', courier_id.courier_number)])
                    mail_activity.sudo().action_done()
                else:
                    courier_id.assign_driver.fbno_total_trip_picked_completed += 1
                    courier_id.assign_driver.fbno_total_trip_picked_pending -= 1
                    courier_id.write({'state': 'Picked', 'status': 'Picked'})
                    mail_activity = request.env['mail.activity'].sudo().search([('res_name', '=', courier_id.courier_number)])
                    mail_activity.sudo().action_done()
                return {
                        'status': 'success', 'courier_id': courier_id.id
                    }
            except:
                return {
                        'status': 'error', 'status_code': 500
                    }

    @http.route([
        '/api/scan_aws/<int:user_id>'],
        type='json', method="POST", auth="user")
    def scan_aws(self, user_id, **kw):
        if user_id:
            courier_id = request.env["courier.courier"].search(
                [
                    ("assign_driver", "=", int(user_id)),
                    ('fbno_tree_id.fbno_air_number', '=', kw.get('pkg_courier_number'))
                ], limit=1)
            if courier_id.status == 'Assigned driver For delivery':
                courier_details = {
                    'courier_id': courier_id and courier_id.id or False,
                    'Courier Number': courier_id.courier_number,
                    "Delivery Type": courier_id.delivery_type,
                    'Sender Name': courier_id.sender_id.name,
                    'Receiver Name': courier_id.receiver_id.name,
                    'Receiver mobile': courier_id.receiver_id.mobile,
                    'Receiver street': courier_id.receiver_id.street,
                    'Receiver street 2': courier_id.receiver_id.street2,
                    'Receiver City': courier_id.receiver_id.city_id.name,
                    'Receiver Area': courier_id.receiver_id.area_id.name,
                    'Booked Date': courier_id.today.date(),
                    'COD amount': courier_id.cod_amount,
                    'No of Piecs': courier_id.fbno_tot_pkges,
                    'Warehouse': courier_id.ware_house_id.name,
                    "status": courier_id.state_express if courier_id.delivery_type == 'express_delivery' else courier_id.state,
                    'packages': [{'name':courier_line.product_description, 'barcode': courier_line.fbno_air_number} for courier_line in courier_id.fbno_tree_id]
                }
                return courier_details
            if courier_id.status == 'Assigned To Driver':
                collection_ship_detail = {
                    'courier_id': courier_id and courier_id.id or False,
                    'Courier Number': courier_id.courier_number,
                    "Delivery Type": courier_id.delivery_type,
                    'Receiver Name': courier_id.receiver_id.name,
                    'Sender Name': courier_id.sender_id.name,
                    'Sender mobile': courier_id.sender_id.mobile,
                    'Sender street': courier_id.sender_id.street,
                    'Sender street 2': courier_id.sender_id.street2,
                    'Sender City': courier_id.sender_id.city_id.name,
                    'Sender Area': courier_id.sender_id.area_id.name,
                    'Booked Date': courier_id.today.date(),
                    'Delivery Total': courier_id.fbno_delivery_total,
                    'COD amount': courier_id.cod_amount,
                    'No of Piecs': courier_id.fbno_tot_pkges,
                    'Total': courier_id.fbno_delivery_total_collected,
                    'Warehouse': courier_id.ware_house_id.name,
                    "status": courier_id.state_express if courier_id.delivery_type == 'express_delivery' else courier_id.state,
                    'packages': [{'name':courier_line.product_description, 'barcode': courier_line.fbno_air_number} for courier_line in courier_id.fbno_tree_id]
                }
                return collection_ship_detail

    @http.route([
        '/api/driver_tracking/<int:user_id>'],
        type='json', method="POST", auth="user")
    def driver_tracking(self, user_id, **kw):
        if user_id:
            partner_id = request.env['res.users'].browse(user_id).partner_id
            partner_id.write(
                {
                    'partner_latitude': kw.get('latitude'),
                    'partner_longitude': kw.get('longitude')
                })
            return {
                'msg': _('Tracking Updated'),
                'status': 'Updated'
            }

    @http.route([
        '/api/driver_fcm_token/<int:user_id>'],
        type='json', method="POST", auth="user")
    def driver_fcm_token(self, user_id, **kw):
        if user_id:
            user_id = request.env['res.users'].browse(user_id).sudo()
            user_id.fbno_fcm_token = kw.get('fcm_token')
            return {
                'msg': _('FCM Token Updated'),
                'status': 'Updated',
            }

    @http.route([
        '/api/application_version/<int:user_id>'],
        type='json', method="POST", auth="user")
    def application_version(self, user_id, **kw):
        if user_id and kw.get('app_version'):
            if request.env['ir.config'].get('app_version') == kw.get('app_version'):
                return {
                    'msg': _('App Version Matched'),
                    'flag': True,
                }
            return {
                    'msg': _('App Version Not Matched'),
                    'flag': False,
                }